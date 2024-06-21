import os
from datetime import datetime, timezone

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import (
    login_required,
    fetch_foods_query,
    fetch_food_by_id,
    prepare_recipe,
    prepare_plan,
    QUERY_NO_RESULTS,
)
# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database mydiet.db
cwd = os.getcwd()
dir_path = os.path.dirname(os.path.realpath(__file__)).replace(os.getcwd(), "")
db = SQL(f"sqlite:///{os.getcwd()}/mydiet.db")

results_to_show = 30


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


"""<---------------------- / ---------------------->"""


@app.route("/")
def index():
    """Show homepage"""
    return render_template("index.html")


"""<---------------------- /my_plans ---------------------->"""


@app.route("/my_plans", methods=["GET", "POST"])
@login_required
def my_plans():
    """Handles the user nutritional plans"""
    # If GET then simply display the users saved plans
    if request.method == "GET":
        return display_plans()
    # If POST it could be a request to create a new plan
    if "add_new_plan" in request.form:
        if not (name := request.form.get("new_plan_name")):
            flash("Name cannot be empty", "warning")
            return redirect("/my_plans")
        if not (description := request.form.get("new_plan_description")):
            flash("Description cannot be empty", "warning")
            return redirect("/my_plans")
        return create_new_plan(name, description)
    # or to delete an existing one
    if plan_id := request.form.get("delete_plan"):
        return delete_plan(plan_id)


def display_plans():
    """Displays the user's saved plans"""
    try:
        plans_db = db.execute(
            "SELECT * FROM plans WHERE user_id = ?", session["user_id"]
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    plans = [
        {
            "id": plan["id"],
            "name": plan["name"],
            "description": plan["description"],
            "date": plan["last_edited"],
        }
        for plan in plans_db
    ]
    return render_template("my_plans.html", plans=plans)


def create_new_plan(name, description):
    """Creates a new plan in the database"""
    try:
        db.execute(
            "INSERT INTO plans (user_id, name, description, last_edited) VALUES (?, ?, ?, ?)",
            session["user_id"],
            name,
            description,
            datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    flash("New plan added to the database", "success")
    return redirect("/my_plans")


def delete_plan(plan_id):
    """Deletes a plan from the database"""
    # Retrieve the owner of the plan
    try:
        plan_owner = db.execute("SELECT user_id FROM plans WHERE id = ?", plan_id)
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    # Check if the plan still exists and if so who is the owner
    if not plan_owner:
        flash("Plan not found", "danger")
        return redirect("/my_plans")
    elif plan_owner[0]["user_id"] != session["user_id"]:
        flash("You tried to delete a plan you don't own", "danger")
        return redirect("/my_plans")
    # Delete the plan
    try:
        db.execute(
            "DELETE FROM plans WHERE id = ?",
            plan_id,
        )
    except Exception as e:
        flash(str(e), "warning")
        return redirect("/my_plans")
    flash("Plan deleted from the database", "success")
    return redirect("/my_plans")


"""<---------------------- /view_plan ---------------------->"""


@app.route("/view_plan", methods=["GET", "POST"])
@login_required
def view_plan():
    """Display selected meal plan"""
    plan_id = request.args.get("plan_id")

    # Check if user has access to this plan
    try:
        user_id = db.execute("SELECT user_id FROM plans WHERE id = ?", plan_id)
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    if not user_id:
        flash("Plan not found", "danger")
        return redirect("/my_plans")
    elif user_id[0]["user_id"] != session["user_id"]:
        flash("You do not have access to this plan", "danger")
        return redirect("/my_plans")

    # Get plan generalities
    try:
        plan_generalities = db.execute(
            "SELECT name, description from plans WHERE id = ?", plan_id
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    if not plan_generalities:
        flash("Plan not found", "danger")
        return redirect("/my_plans")
    plan_name = plan_generalities[0]["name"]
    plan_description = plan_generalities[0]["description"]
    try:
        plan_entries = db.execute(
            "SELECT id_food, id_recipe, meal, amount FROM plans_entries WHERE id_plan = ?",
            plan_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")

    # Fetch all entries data from the API and proceed to elaborate them
    elaborated_plan_entries = prepare_plan(plan_entries, db)
    if isinstance(elaborated_plan_entries, str):
        flash(elaborated_plan_entries, "danger")
        return redirect("/")

    return render_template(
        "view_plan.html",
        plan_id=plan_id,
        plan_name=plan_name,
        plan_description=plan_description,
        breakfast=elaborated_plan_entries["breakfast"],
        lunch=elaborated_plan_entries["lunch"],
        dinner=elaborated_plan_entries["dinner"],
        snack=elaborated_plan_entries["snack"],
    )


"""<---------------------- /update_plan ---------------------->"""


@app.route("/update_plan", methods=["GET", "POST"])
@login_required
def update_plan():
    """Update selected plan"""
    plan_id = request.args.get("plan_id")

    # Check if the user requesting the view the plan is the owner
    user_id = db.execute("SELECT user_id FROM plans WHERE id = ?", plan_id)
    if not user_id:
        flash("Plan not found", "danger")
        return redirect("/my_plans")
    if user_id[0]["user_id"] != session["user_id"]:
        flash("You do not have access to this plan", "danger")
        return redirect("/my_plans")

    # Was the request to change name?
    if "update_plan_name" in request.form:
        new_plan_name = request.form.get("plan_name")
        if new_plan_name == "":
            flash("Name cannot be empty", "warning")
            return redirect(f"/view_plan?plan_id={plan_id}")
        return change_plan_name(new_plan_name, plan_id)

    # Was the request to change description?
    if "update_plan_description" in request.form:
        new_plan_description = request.form.get("plan_description")
        if new_plan_description == "":
            flash("Description cannot be empty", "danger")
            return redirect(f"/view_plan?plan_id={plan_id}")
        return change_plan_description(new_plan_description, plan_id)

    # Was the request to delete an entry?
    if entry_id := request.form.get("remove_food"):
        meal = request.args.get("meal")
        simple_food = request.args.get("simple_food")
        return remove_entry_plan(entry_id, meal, simple_food, plan_id)

    # The user could have requested to change the amount of a certain ingredient
    if "increase_amount" in request.form:
        simple_food = request.args.get("simple_food")
        id_food = request.form.get("increase_amount")
        meal = request.args.get("meal")
        return increase_amount_ingredient_plan(meal, id_food, simple_food, plan_id)
    if "decrease_amount" in request.form:
        simple_food = request.args.get("simple_food")
        id_food = request.form.get("decrease_amount")
        meal = request.args.get("meal")
        return decrease_amount_ingredient_plan(meal, id_food, simple_food, plan_id)

    # Was the request to add an entry?
    if "add_new_entry" in request.form:
        new_ingredient_amount = request.form.get("new_ingredient_amount")
        meal = request.args.get("meal")
        new_entry_id = request.args.get("new_entry_id")
        simple_food = request.args.get("simple_food")
        try:
            new_ingredient_amount = round(float(new_ingredient_amount), 3)
        except ValueError:
            flash("Please enter a valid number as the amount", "warning")
            return redirect(f"/search_new_entry_plan?plan_id={plan_id}&meal={meal}")
        return add_entry_plan(
            new_ingredient_amount, meal, new_entry_id, simple_food, plan_id
        )


def change_plan_name(new_plan_name, plan_id):
    """Change plan name"""
    try:
        db.execute(
            "UPDATE plans SET name = ?, last_edited = ? WHERE id = ?",
            new_plan_name,
            datetime.now(timezone.utc).strftime("%d/%m/%Y"),
            plan_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    flash("Plan name saved", "success")
    return redirect(f"/view_plan?plan_id={plan_id}")


def change_plan_description(new_plan_description, plan_id):
    """Change plan description"""
    try:
        db.execute(
            "UPDATE plans SET description = ?, last_edited = ? WHERE id = ?",
            new_plan_description,
            datetime.now(timezone.utc).strftime("%d/%m/%Y"),
            plan_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    flash("Plan description saved", "success")
    return redirect(f"/view_plan?plan_id={plan_id}")


def remove_entry_plan(entry_id, meal, simple_food, plan_id):
    """Remove an entry from the selected plan"""
    id_selector = "id_recipe" if simple_food == "False" else "id_food"
    try:
        db.execute(
            f"DELETE FROM plans_entries WHERE {id_selector} = ? and meal = ? and id_plan = ?",
            entry_id,
            meal,
            plan_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    flash("Ingredient removed from the recipe", "success")
    return redirect(f"/view_plan?plan_id={plan_id}")


def increase_amount_ingredient_plan(meal, id_food, simple_food, plan_id):
    """Increase the amount of an ingredient in the plan by 1"""
    id_selector = "id_recipe" if simple_food == "False" else "id_food"
    try:
        old_amount = db.execute(
            f"SELECT id, amount FROM plans_entries WHERE id_plan = ? and {id_selector} = ? and meal = ?",
            plan_id,
            id_food,
            meal,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    if old_amount is not None:
        try:
            db.execute(
                "UPDATE plans_entries SET amount = ? WHERE id = ?",
                round(old_amount[0]["amount"] + 1, 1),
                old_amount[0]["id"],
            )
            flash("Amount increased", "success")
            return redirect(f"/view_plan?plan_id={plan_id}")
        except Exception as e:
            flash(str(e), "danger")
            return redirect("/")
    else:
        flash("Ingredient not found in the recipe", "danger")
        return redirect(f"/view_plan?plan_id={plan_id}")


def decrease_amount_ingredient_plan(meal, id_food, simple_food, plan_id):
    """Decrease the amount of an ingredient in the plan by 1"""
    id_selector = "id_recipe" if simple_food == "False" else "id_food"
    try:
        old_amount = db.execute(
            f"SELECT id, amount FROM plans_entries WHERE id_plan = ? and {id_selector} = ? and meal = ?",
            plan_id,
            id_food,
            meal,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    if old_amount is not None:
        if float(old_amount[0]["amount"]) > 1:
            try:
                db.execute(
                    "UPDATE plans_entries SET amount = ? WHERE id = ?",
                    round(old_amount[0]["amount"] - 1, 1),
                    old_amount[0]["id"],
                )
                flash("Amount decreased", "success")
                return redirect(f"/view_plan?plan_id={plan_id}")
            except Exception as e:
                flash(str(e), "danger")
                return redirect("/")
        else:
            flash(
                "Cannot decrease amount below 1, use the proper button to delete the ingredient",
                "warning",
            )
            return redirect(f"/view_plan?plan_id={plan_id}")
    else:
        flash("Ingredient not found in the recipe", "danger")
        return redirect(f"/view_plan?plan_id={plan_id}")


def add_entry_plan(new_ingredient_amount, meal, new_entry_id, simple_food, plan_id):
    """Add an entry to the plan"""
    id_selector = "id_recipe" if simple_food == "False" else "id_food"
    try:
        # Check if the entry already exists, if so just update the amount
        if previous_amount := db.execute(
            f"SELECT id, amount FROM plans_entries WHERE id_plan = ? and {id_selector} = ? and meal = ?",
            plan_id,
            new_entry_id,
            meal,
        ):
            db.execute(
                "UPDATE plans_entries SET amount = ? WHERE id = ?",
                new_ingredient_amount + float(previous_amount[0]["amount"]),
                previous_amount[0]["id"],
            )
        else:
            db.execute(
                f"INSERT INTO plans_entries (id_plan, {id_selector}, meal, amount) VALUES (?, ?, ?, ?)",
                plan_id,
                new_entry_id,
                meal,
                new_ingredient_amount,
            )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    flash("New entry added to the plan", "success")
    return redirect(f"/view_plan?plan_id={plan_id}")


"""<---------------------- /search_new_entry_plan ---------------------->"""


@app.route("/search_new_entry_plan", methods=["GET", "POST"])
@login_required
def search_new_entry_plan():
    """Handle requests regarding the search_new_entry_plan.html page"""
    plan_id = request.args.get("plan_id")
    meal = request.args.get("meal")
    
    # Check if the user requesting the view the plan is the owner
    user_id = db.execute("SELECT user_id FROM plans WHERE id = ?", plan_id)
    if not user_id:
        flash("Plan not found", "danger")
        return redirect("/my_plans")
    if user_id[0]["user_id"] != session["user_id"]:
        flash("You do not have access to this plan", "danger")
        return redirect("/my_plans")

    # Was a search requested?
    if "add_entry_plan_button" in request.form:
        # Check if query isn't empty
        if not (query := request.form.get("add_entry_plan_input")):
            flash("Please enter a search query", "warning")
            return render_template(
                "search_new_entry_plan.html", plan_id=plan_id, meal=meal
            )

        if request.form.get("inline_radio") == "inline_radio_food":
            return search_new_entry_plan_food(query, plan_id, meal)
        else:
            return search_new_entry_plan_recipes(query, plan_id, meal)

    return render_template(
        "search_new_entry_plan.html", plan_id=plan_id, meal=meal, results=""
    )


def search_new_entry_plan_food(query, plan_id, meal):
    """Display results if the request was for simple food"""
    foods = fetch_foods_query(query)
    # Has there been any error?
    if isinstance(foods, str):
        if foods == QUERY_NO_RESULTS:
            flash(foods, "warning")
            return redirect(f"/add_entry_plan?plan_id={plan_id}&meal={meal}")
        else:
            flash(foods, "danger")
            return redirect("/")
    else:
        flash(
            f"Displaying the top {len(foods)} results for query: {query}",
            "primary",
        )
        return render_template(
            "search_new_entry_plan.html",
            food=query,
            plan_id=plan_id,
            meal=meal,
            results=foods,
            radio_to_check=1,
        )


def search_new_entry_plan_recipes(query, plan_id, meal):
    """Display results if the request was for recipes"""
    # Retrieve data of servings belonging to the user that have "query" inside their name
    try:
        recipes_data = db.execute(
            "SELECT id, name, total_servings FROM recipes where name like ? and user_id = ?",
            f"%{query}%",
            session["user_id"],
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    # If no recipes were found...
    if not recipes_data:
        flash("No recipes found for the selected query", "warning")
        return render_template(
            "search_new_entry_plan.html",
            food=query,
            plan_id=plan_id,
            meal=meal,
            radio_to_check=2,
        )
    # Build the array of Recipe objects corresponding to the retrieved recipes
    recipes = []
    for recipe in recipes_data:
        # if recipe was already loaded in session we simply retrieve it
        if f"recipe_id_{recipe['id']}" in session:
            recipes.append(session[f"recipe_id_{recipe['id']}"])
        else:
            recipes.append(load_recipe_data(recipe["id"]))
            # Check if any error was reported by the API
            if isinstance(recipes[-1], str):
                flash(recipes[-1], "danger")
                return redirect("/")

            session[f"recipe_id_{recipe['id']}"] = recipes[-1]
    flash(
        f'Found {len(recipes)} recipes containing "{query}" inside their name',
        "primary",
    )
    foods = [
        {
            "food_id": recipes_data[i]["id"],
            "name": recipes_data[i]["name"],
            "brand": "",
            "serving_description": f"{recipes_data[i]['total_servings']} servings",
            "calories": recipes[i].tot_calories,
            "carbohydrate": recipes[i].tot_carbohydrate,
            "fat": recipes[i].tot_fat,
            "protein": recipes[i].tot_protein,
            "measurement_description": "servings",
        }
        for i in range(len(recipes))
    ]
    return render_template(
        "search_new_entry_plan.html",
        food=query,
        plan_id=plan_id,
        meal=meal,
        results=foods,
        radio_to_check=2,
    )


def load_recipe_data(recipe_id):
    """Given a recipe id, this function returns the corresponding Recipe object or a string describing any error encountered"""
    # Retrieve all the ingredients for the recipe
    try:
        recipe_entries = db.execute(
            "SELECT id_food, amount FROM recipes_entries WHERE id_recipe = ?", recipe_id
        )
    except Exception as e:
        return str(e)

    # Fetch data from the API for each ingredient and prepare the list
    ingredients = [fetch_food_by_id(entry["id_food"]) for entry in recipe_entries]

    # Check if any error was reported by the API
    if isinstance(ingredients, str):
        return ingredients

    amounts = [entry["amount"] for entry in recipe_entries]
    # Weight the ingredients macros by the respective amounts
    # Return value is a Recipe object
    return prepare_recipe(ingredients, amounts)


"""<---------------------- /my_recipes ---------------------->"""


@app.route("/my_recipes", methods=["GET", "POST"])
@login_required
def my_recipes():
    """Handles the user personal recipes"""
    # If GET then simply display the users saved recipes
    if request.method == "GET":
        return display_recipes()
    # If post it could either be to add a new recipe
    if "add_new_recipe" in request.form:
        if not (name := request.form.get("new_recipe_name")):
            flash("Name cannot be empty", "warning")
            return redirect("/my_recipes")
        total_servings = request.form.get("new_recipe_total_servings")
        try:
            total_servings = int(total_servings)
        except ValueError:
            flash("Please enter a valid number as total servings", "warning")
            return redirect("/my_recipes")
        return create_new_recipe(name, total_servings)
    # or to delete an existing one
    if recipe_id := request.args.get("recipe_id"):
        return delete_recipe(recipe_id)


def display_recipes():
    """Display the user's saved recipes"""
    try:
        recipes_db = db.execute(
            "SELECT * FROM recipes WHERE user_id = ?", session["user_id"]
        )
    except Exception as e:
        flash(e, "danger")
        redirect("/")
    recipes = [
        {
            "id": recipe["id"],
            "name": recipe["name"],
            "total_servings": recipe["total_servings"],
        }
        for recipe in recipes_db
    ]
    return render_template("my_recipes.html", recipes=recipes)


def create_new_recipe(name, total_servings):
    """Create a new recipe in the database"""
    try:
        db.execute(
            "INSERT INTO recipes (user_id, name, total_servings) VALUES (?, ?, ?)",
            session["user_id"],
            name,
            total_servings,
        )
    except Exception as e:
        flash(e, "danger")
        return redirect("/")
    return redirect("/my_recipes")


def delete_recipe(recipe_id):
    """Delete a recipe from the database"""
    try:
        db.execute(
            "DELETE FROM recipes WHERE user_id = ? AND id = ?",
            session["user_id"],
            recipe_id,
        )
    except Exception as e:
        flash("e", "danger")
        return redirect("/")
    # Remove the recipe from the session if it was loaded
    if f"recipe_id_{recipe_id}" in session:
        session.pop(f"recipe_id_{recipe_id}")
    return redirect("/my_recipes")


"""<---------------------- /view_recipe ---------------------->"""


@app.route("/view_recipe", methods=["GET", "POST"])
@login_required
def view_recipe():
    """Display selected meal plan"""
    recipe_id = request.args.get("recipe_id")
    # Check if the user requesting the recipe is the owner
    user_id = db.execute("SELECT user_id FROM recipes WHERE id = ?", recipe_id)
    if not user_id:
        flash("Recipe not found", "danger")
        return redirect("/my_recipes")
    if user_id[0]["user_id"] != session["user_id"]:
        flash("You do not have access to this recipe", "danger")
        return redirect("/my_recipes")

    try:
        recipe_generalities = db.execute(
            "SELECT name, total_servings FROM recipes WHERE id = ?", recipe_id
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")

    if not recipe_generalities:
        flash("Recipe not found", "danger")
        return redirect("/my_recipes")
    recipe_name = recipe_generalities[0]["name"]
    recipe_total_servings = recipe_generalities[0]["total_servings"]

    # Has the current recipe already been loaded in session? If not...
    if f"recipe_id_{recipe_id}" not in session:
        # ...load it with the use of fatsecret API
        recipe = load_recipe_data(recipe_id)
        if isinstance(recipe, str):
            flash(recipe, "danger")
            return redirect("/")
        # And add it to the session
        session[f"recipe_id_{recipe_id}"] = recipe
    else:
        recipe = session[f"recipe_id_{recipe_id}"]

    # The user could have requested to search for a new ingredient
    if "new_ingredient_query" in request.form:
        search_ingredient = request.form.get("new_ingredient_query")
        if search_ingredient == "":
            flash("Please enter an ingredient to search", "warning")
            return redirect(f"/view_recipe?recipe_id={recipe_id}")
        # Expected return value is an array of Food objects
        search_results = fetch_foods_query(search_ingredient, n_results=results_to_show)

        if isinstance(search_results, str):
            if search_results == QUERY_NO_RESULTS:
                flash(search_results, "warning")
                return redirect(f"/view_recipe?recipe_id={recipe_id}")
            else:
                flash(search_results, "danger")
                return redirect("/")
        else:
            flash(
                f"Displaying the top {len(search_results)} results for query: {search_ingredient}",
                "primary",
            )
        return render_template(
            "view_recipe.html",
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            recipe_total_servings=recipe_total_servings,
            recipe=recipe,
            search_results=search_results,
        )

    # If no search query then simply display the list of current ingredients
    return render_template(
        "view_recipe.html",
        recipe_id=recipe_id,
        recipe_name=recipe_name,
        recipe_total_servings=recipe_total_servings,
        recipe=recipe,
    )


"""<---------------------- /update_recipe ---------------------->"""


@app.route("/update_recipe", methods=["GET", "POST"])
@login_required
def update_recipe():
    """Update selected recipe"""
    recipe_id = request.args.get("recipe_id")

    # Check if the user requesting the recipe is the owner
    user_id = db.execute("SELECT user_id FROM recipes WHERE id = ?", recipe_id)
    if not user_id:
        flash("Recipe not found", "danger")
        return redirect("/my_recipes")
    if user_id[0]["user_id"] != session["user_id"]:
        flash("You do not have access to this recipe", "danger")
        return redirect("/my_recipes")

    # Was the request to change name?
    if "update_recipe_generalities" in request.form:
        new_name = request.form.get("recipe_name")
        new_total_servings = request.form.get("recipe_total_servings")
        if new_name == "":
            flash("Name cannot be empty", "warning")
            return redirect(f"/view_recipe?recipe_id={recipe_id}")
        try:
            int(new_total_servings)
        except ValueError:
            flash("Please enter a valid number as total servings", "warning")
            return redirect(f"/view_recipe?recipe_id={recipe_id}")
        return change_recipe_generalities(new_name, new_total_servings, recipe_id)

    # Was the request to remove an ingredient?
    if entry_id := request.form.get("remove_ingredient"):
        return remove_entry_recipe(entry_id, recipe_id)

    # The user could have requested to change the amount of a certain ingredient
    if "increase_amount" in request.form:
        id_food = request.form.get("increase_amount")
        return increase_amount_ingredient_recipe(id_food, recipe_id)
    if "decrease_amount" in request.form:
        id_food = request.form.get("decrease_amount")
        return decrease_amount_ingredient_recipe(id_food, recipe_id)

    # Was the request to add an ingredient?
    if "add_new_entry" in request.form:
        new_ingredient_amount = request.form.get("new_ingredient_amount")
        new_ingredient_id = request.args.get("new_ingredient_id")
        try:
            new_ingredient_amount = round(float(new_ingredient_amount), 3)
        except ValueError:
            flash("Please enter a valid number", "warning")
            return redirect(f"/view_recipe?recipe_id={recipe_id}")
        return add_entry_recipe(new_ingredient_amount, new_ingredient_id, recipe_id)


def change_recipe_generalities(new_name, new_total_servings, recipe_id):
    """Update name and total servings of the selected recipe"""
    try:
        db.execute(
            "UPDATE recipes SET name = ?, total_servings = ? WHERE id = ?",
            new_name,
            new_total_servings,
            recipe_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    flash("Recipe name and total servings saved", "success")
    return redirect(f"/view_recipe?recipe_id={recipe_id}")


def remove_entry_recipe(entry_id, recipe_id):
    """Remove an entry from the selected recipe"""
    try:
        db.execute(
            "DELETE FROM recipes_entries WHERE id_food = ? and id_recipe = ?",
            entry_id,
            recipe_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    flash("Ingredient removed from the recipe", "success")
    # Recipe in session is now outdated
    if f"recipe_id_{recipe_id}" in session:
        session.pop(f"recipe_id_{recipe_id}")
    return redirect(f"/view_recipe?recipe_id={recipe_id}")


def increase_amount_ingredient_recipe(id_food, recipe_id):
    """Increase the amount of an ingredient in the selected recipe by 1"""
    try:
        old_amount = db.execute(
            "SELECT id, amount FROM recipes_entries WHERE id_food = ? and id_recipe = ?",
            id_food,
            recipe_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    if old_amount is not None:
        try:
            db.execute(
                "UPDATE recipes_entries SET amount = ? WHERE id = ?",
                round(old_amount[0]["amount"] + 1, 1),
                old_amount[0]["id"],
            )
            if f"recipe_id_{recipe_id}" in session:
                session.pop(f"recipe_id_{recipe_id}")
            return redirect(f"/view_recipe?recipe_id={recipe_id}")
        except Exception as e:
            flash(str(e), "danger")
            return redirect("/")
    else:
        flash("Ingredient not found in the recipe", "danger")
        return redirect(f"/view_recipe?recipe_id={recipe_id}")


def decrease_amount_ingredient_recipe(id_food, recipe_id):
    """Decrease the amount of an ingredient in the selected recipe by 1"""
    try:
        old_amount = db.execute(
            "SELECT id, amount FROM recipes_entries WHERE id_food = ? and id_recipe = ?",
            id_food,
            recipe_id,
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    if old_amount is not None:
        if float(old_amount[0]["amount"]) > 1:
            try:
                db.execute(
                    "UPDATE recipes_entries SET amount = ? WHERE id = ?",
                    round(old_amount[0]["amount"] - 1, 1),
                    old_amount[0]["id"],
                )
                if f"recipe_id_{recipe_id}" in session:
                    session.pop(f"recipe_id_{recipe_id}")
                return redirect(f"/view_recipe?recipe_id={recipe_id}")
            except Exception as e:
                flash(str(e), "danger")
                return redirect("/")
        else:
            flash(
                "Cannot decrease amount below 1, use the proper button to delete the ingredient",
                "warning",
            )
            return redirect(f"/view_recipe?recipe_id={recipe_id}")
    else:
        flash("Ingredient not found in the recipe", "danger")
        return redirect(f"/view_recipe?recipe_id={recipe_id}")


def add_entry_recipe(new_ingredient_amount, new_ingredient_id, recipe_id):
    """Add an entry to the selected recipe"""
    try:
        if previous_amount := db.execute(
            "SELECT id, amount FROM recipes_entries WHERE id_food = ? and id_recipe = ?",
            new_ingredient_id,
            recipe_id,
        ):
            db.execute(
                "UPDATE recipes_entries SET amount = ? WHERE id=?",
                new_ingredient_amount + float(previous_amount[0]["amount"]),
                previous_amount[0]["id"],
            )

        else:
            db.execute(
                "INSERT INTO recipes_entries (id_recipe, id_food, amount) VALUES (?, ?, ?)",
                recipe_id,
                new_ingredient_id,
                new_ingredient_amount,
            )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")
    # Recipe in session is now outdated
    if f"recipe_id_{recipe_id}" in session:
        session.pop(f"recipe_id_{recipe_id}")
    return redirect(f"/view_recipe?recipe_id={recipe_id}")


"""<---------------------- /search_food ---------------------->"""


@app.route("/search_food", methods=["GET", "POST"])
@login_required
def search_food():
    """Search food based on the user query and renders search_food.html accordingly"""
    if request.method == "GET":
        return render_template("search_food.html")

    food = request.form.get("food") or ""
    brand = request.form.get("brand") or ""
    # Currently not implemented in the html page
    max_results = request.form.get("max_results") or results_to_show

    if food == "" and brand == "":
        flash("Please enter something to search", "warning")
        return render_template("search_food.html")

    # Default advanced search values
    accept_generic = True
    accept_brand = True
    radio_to_check = 1

    # Change advanced search values
    if request.form.get("inline_radio") == "inline_radio_generic":
        accept_brand = False
        radio_to_check = 2
    elif request.form.get("inline_radio") == "inline_radio_branded":
        accept_generic = False
        radio_to_check = 3

    # Fetch results
    data_fetched = fetch_foods_query(
        name=food,
        brand=brand,
        accept_brand=accept_brand,
        accept_generic=accept_generic,
        n_results=max_results,
    )
    # If there was an error or the query produced zero results
    if isinstance(data_fetched, str):
        if data_fetched == QUERY_NO_RESULTS:
            flash(data_fetched, "warning")
            return render_template(
                "search_food.html",
                food=food,
                brand=brand,
                radio_to_check=radio_to_check,
            )
        else:
            flash(data_fetched, "danger")
            return redirect("/")

    # Else display results
    flash(f"Your query produced {len(data_fetched)} results", "primary")
    return render_template(
        "search_food.html",
        query_result=data_fetched,
        food=food,
        brand=brand,
        radio_to_check=radio_to_check,
    )


"""<---------------------- /nutrition_facts ---------------------->"""


@app.route("/nutrition_facts", methods=["GET", "POST"])
def nutrition_facts():
    """Display nutrition facts for selected food"""
    food_id = request.args.get("food_id")
    data_fetched = fetch_food_by_id(food_id=food_id)
    if isinstance(data_fetched, str):
        flash(data_fetched, "danger")
        return redirect("/")

    return render_template("nutrition_facts.html", item=data_fetched)


"""<---------------------- /login ---------------------->"""


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    if request.method == "GET":
        return render_template("login.html")

    # Ensure username was submitted
    if not request.form.get("username"):
        flash("Must provide an username", "warning")
        return render_template("login.html")

    # Ensure password was submitted
    if not request.form.get("password"):
        flash("Must provide password", "warning")
        return render_template("login.html")

    # Query database for username
    try:
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/")

    # Ensure username exists and password is correct
    if len(rows) != 1 or not check_password_hash(
        rows[0]["password"], request.form.get("password")
    ):
        flash("Invalid username and/or password", "danger")
        return render_template("login.html")

    # Remember which user has logged in
    session["user_id"] = rows[0]["id"]

    # Redirect user to home page
    flash("Successfully logged in", "success")
    return redirect("/")


"""<---------------------- /logout ---------------------->"""


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Successfully logged out", "info")
    return redirect("/")


"""<---------------------- /register ---------------------->"""


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    username = request.form.get("username")
    password = request.form.get("password")
    password_c = request.form.get("confirmation")

    if username == "" or password == "" or password_c == "":
        flash("All fields are required", "warning")
        return render_template("register.html")

    if password != password_c:
        flash("Passwords don't match", "warning")
        return render_template("register.html")

    password_hashed = generate_password_hash(password)

    try:
        db.execute(
            "insert into users (username, password) values (?, ?)",
            username,
            password_hashed,
        )
    except Exception:
        flash("Username already exists", "warning")
        return render_template("register.html")

    flash("Registration completed, please log in", "success")
    return render_template("login.html")


# For debug!
if __name__ == "__main__":
    app.run(debug=True)

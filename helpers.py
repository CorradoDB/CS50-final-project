from flask import redirect, session
from rauth import OAuth1Service
from functools import wraps
from dataclasses import dataclass, field
from keys import fs_consumer_key, fs_consumer_secret
import numpy as np
import re

QUERY_NO_RESULTS = "QUERY PRODUCED ZERO RESULTS, TRY ANOTHER"


@dataclass
class Food:
    food_id: str = ""
    img_url: str = ""
    name: str = ""
    serving_description: str = ""
    number_of_units: float = 0
    measurement_description: str = ""
    calories: float = 0
    fat: float = 0
    carbohydrate: float = 0
    protein: float = 0
    brand: str = ""
    saturated_fat: str = "N/A"
    trans_fat: str = "N/A"
    polyunsaturated_fat: str = "N/A"
    monounsaturated_fat: str = "N/A"
    cholesterol: str = "N/A"
    sodium: str = "N/A"
    fiber: str = "N/A"
    sugar: str = "N/A"
    vitamin_d: str = "N/A"
    calcium: str = "N/A"
    iron: str = "N/A"
    potassium: str = "N/A"
    vitamin_a: str = "N/A"
    vitamin_c: str = "N/A"
    img_url: str = ""


@dataclass
class Recipe:
    tot_calories: float = 0
    tot_fat: float = 0
    tot_carbohydrate: float = 0
    tot_protein: float = 0
    ingredients: list = field(default_factory=list)


# redirects to /login when user_id not in session
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def get_session():
    def establish_connection_API_fs():
        """
        Establish connection to fatsecret API and returns the session object, or a string describing any error reported by the API
        """
        # Unauthenticated session is enough for the scope of this project
        oauth = OAuth1Service(
            name="fatsecret",
            consumer_key=fs_consumer_key,
            consumer_secret=fs_consumer_secret,
            request_token_url="https://www.fatsecret.com/oauth/request_token",
            access_token_url="https://www.fatsecret.com/oauth/access_token",
            authorize_url="https://www.fatsecret.com/oauth/authorize",
            base_url="https://platform.fatsecret.com/rest/server.api",
        )

        try:
            session_api = oauth.get_session()
        except Exception as e:
            return str(e)

        return session_api

    """
    Prepare the fatsecret API session either from the cache or by establishing a new one.
    Returns the session object, or a string describing any error reported by the API
    """
    if "session_api" in session:
        session_api = session["session_api"]
    else:
        session_api = establish_connection_API_fs()
        if isinstance(session_api, str):
            return session_api
        session["session_api"] = session_api
    return session_api


def call_API(query=None, food_id=None):
    """
    Call the API and return its response, provide either a query or the food_id
    """
    session_api = get_session()
    if issubclass(type(session_api), Exception):
        return session_api

    if query is not None:
        params = {
            "method": "foods.search.v3",
            "search_expression": f"{query['name']} {query['brand']}",
            "format": "json",
            "page_number": query["page_number"],
            "max_results": "50",
            "include_food_images": "true",
        }
    else:
        params = {
            "method": "food.get",
            "food_id": food_id,
            "format": "json",
            "include_food_images": "true",
        }

    try:
        response = (
            session_api.get(
                "https://platform.fatsecret.com/rest/server.api", params=params
            )
        ).json()
    except Exception as e:
        return str(e)

    if "error" in response:
        # Any other error beside Invalid/expired timestamp is returned
        if response["error"]["code"] != "6":
            return f"Error Code: {response['error']['code']} & Message: {response['error']['message']}"
        # If code 6 there should be a previous api session in flask session, if not return the error
        if "session_api" not in session:
            return f"Error Code: {response['error']['code']} & Message: {response['error']['message']}"
        # Pop the old api session and try again
        session.pop("session_api")
        return call_API(query, food_id)

    return response


def fetch_foods_query(
    name="",
    brand="",
    accept_generic=True,
    accept_brand=True,
    n_results=30,
    page_number=0,
):
    """
    fetch_foods_query tries to recover "n_results" amount of food that matches the provided name and brand.
    Set accept_generic to False if you only want branded food. Set accept_brand to False if you only want generic food.
    Setting both to False will return "QUERY_NO_RESULTS".
    IMPORTANT: do not modify "table" parameter, it's purpose is only for recursive calls

    The API can return either a dictionary with key "error" in case of a problem, or a list of results,
    for a more detailed explanation of the format visit https://platform.fatsecret.com/docs/v3/foods.search

    fetch_food_query returns a string if the connection failed or the query produced no results,
    else a properly populated Food object.
    """
    # Check if input parameters are valid
    if not accept_generic and not accept_brand:
        return QUERY_NO_RESULTS

    # Call the API
    response = call_API(
        query={"name": name, "brand": brand, "page_number": page_number}
    )
    # If response is a string there was an error
    if isinstance(response, str):
        return response

    # Check if there query fetched something valid
    if response["foods_search"]["results"] is None:
        return QUERY_NO_RESULTS

    foods = []
    for food_data in response["foods_search"]["results"]["food"]:
        # Drop current food if generic and user requested only branded
        if (not accept_generic) and food_data["food_type"] == "Generic":
            continue
        # Drop current food if branded and user requested only generic
        if (not accept_brand) and food_data["food_type"] == "Brand":
            continue
        # Drop current food if requested a specific brand and there is no match
        if brand != "":
            if "brand_name" not in food_data:
                continue
            elif brand.lower() not in food_data["brand_name"].lower():
                continue

        # notice that sometimes serving isn't an array but just the default serving
        try:
            food = parse_macro(food_data["servings"]["serving"][0])
        except Exception:
            food = parse_macro(food_data["servings"]["serving"])

        # Check if the returned values isn't None
        if food is not None:
            parse_generic_info(food, food_data)

            # Add the Food to session and to the list foods
            session["food_id_" + food_data["food_id"]] = food
            foods.append(food)

            # If the requested quota is met we can drop the rest of the results
            if len(foods) == n_results:
                return foods

    # Reaching this point means we still haven't found the requested number of results
    # unless we already inspected 50*10 results, we proceed with a new request for the
    # remaining missing results starting from the next available page
    # notice that if the response had less than 50 results then it means there are no more pages to request
    if len(response["foods_search"]["results"]["food"]) == 50 and page_number < 9:
        n_results -= len(foods)
        new_page = fetch_foods_query(
            name,
            brand,
            accept_generic,
            accept_brand,
            n_results=n_results,
            page_number=page_number + 1,
        )
        # If there was no error we concatenate the two lists and return them
        if isinstance(new_page, str):
            return foods
        else:
            return np.concatenate((foods, new_page), axis=None)
    return foods


def fetch_food_by_id(food_id=""):
    """
    Fetch the data relative to a specific food by proving its id relative to fatsecret database
    Details on the format of the response at https://platform.fatsecret.com/docs/v4/food.get.
    The returned value is a Food or a string explaining eventual error reported by the API
    """
    # If the food data was already in session we simply return it
    if f"food_id_{food_id}" in session:
        return session[f"food_id_{food_id}"]

    # Call the API
    response = call_API(food_id=food_id)

    # If response is a string then there was an error
    if isinstance(response, str):
        return response
    else:
        response = response["food"]

    # Parse the default serving, index 0, and copy the key:value from it into food
    # notice that sometimes serving isn't an array but just the default serving
    try:
        food = parse_macro(response["servings"]["serving"][0])
    except Exception:
        food = parse_macro(response["servings"]["serving"])
    # In this case parse_macro will never return None because if we have a food_id it means that
    # it was previously fetched by another valid API call
    parse_generic_info(food, response)

    # Temporary save the current food in session
    session[f"food_id_{food_id}"] = food
    return food


def parse_macro(food_data):
    """
    Receive raw data fetched from the API, and transfer the macro into a Food object.
    If the macro format was valid then returns the Food object, otherwise returns None
    """
    food = Food()
    # <---------------- Guaranteed values ---------------->

    # Usual format for serving_description is "x y" where x is the amount and y the serving type
    # but there are many exceptions and fatsecret doesn't provide any information on this,
    # therefore the most frequent are accounted for while the rest are simply discarded

    # Note that we are forced to use serving_description because it's the only one guaranteed to be complete for every food

    # Some food have "irrelevant" information inside parentheses, we first remove those if present
    pattern = r" \([^()]*\)"
    serving_desc = re.sub(pattern, "", food_data["serving_description"])
    # Is the format "x y" or something else?
    index_to_split = serving_desc.find(" ")
    if index_to_split == -1:
        # Anything but xy is discarded
        # We first search for the beginning of y, so index of first alphabetical char
        try:
            index_to_split = serving_desc.find(next(filter(str.isalpha, serving_desc)))
        except StopIteration:
            return None
        # Then we check if x exists (first char must not be alphabetical)
        if index_to_split == 0:
            return None
        # Now we are ready to split and save the measurement description
        food.measurement_description = serving_desc[index_to_split:]
    else:
        food.measurement_description = serving_desc[index_to_split + 1 :]
    # Now we can try to eliminate another peace of "irrelevant" information: anything after the character ","
    pattern = r",\s*\S.*"
    food.measurement_description = re.sub(pattern, "", food.measurement_description)
    food.serving_description = f"{serving_desc[:index_to_split]} {food.measurement_description}"

    # Now we only need to check if x is a valid number, or something in the format 1-b/c
    try:
        food.number_of_units = round(float(serving_desc[:index_to_split]), 2)
    except ValueError:
        try:
            div1, div2 = serving_desc[:index_to_split].split("/")
            if div1.find("-") != -1:
                extra, div1 = div1.split("-")
            else:
                extra = 0
            food.number_of_units = round(
                (float(div1)) / (float(div2)) + float(extra), 2
            )
        except ValueError:
            return None

    food.calories = round(float(food_data["calories"]), 2)
    food.protein = round(float(food_data["protein"]), 2)
    food.carbohydrate = round(float(food_data["carbohydrate"]), 2)
    food.fat = round(float(food_data["fat"]), 2)

    # <---------------- Not guaranteed values ---------------->
    if "saturated_fat" in food_data:
        food.saturated_fat = food_data["saturated_fat"]
    if "trans_fat" in food_data:
        food.trans_fat = food_data["trans_fat"]
    if "polyunsaturated_fat" in food_data:
        food.polyunsaturated_fat = food_data["polyunsaturated_fat"]
    if "monounsaturated_fat" in food_data:
        food.monounsaturated_fat = food_data["monounsaturated_fat"]
    if "cholesterol" in food_data:
        food.cholesterol = food_data["cholesterol"]
    if "sodium" in food_data:
        food.sodium = food_data["sodium"]
    if "fiber" in food_data:
        food.fiber = food_data["fiber"]
    if "sugar" in food_data:
        food.sugar = food_data["sugar"]
    if "vitamin_d" in food_data:
        food.vitamin_d = food_data["vitamin_d"]
    if "calcium" in food_data:
        food.calcium = food_data["calcium"]
    if "iron" in food_data:
        food.iron = food_data["iron"]
    if "potassium" in food_data:
        food.potassium = food_data["potassium"]
    if "vitamin_a" in food_data:
        food.vitamin_a = food_data["vitamin_a"]
    if "vitamin_c" in food_data:
        food.vitamin_c = food_data["vitamin_c"]

    return food


def parse_generic_info(food, food_data):
    """
    Receive raw data fetched from the API, and transfer the generic information into a provided Food object
    """
    food.name = food_data["food_name"]
    if food_data["food_type"] == "Brand":
        food.brand = food_data["brand_name"]
    food.food_id = food_data["food_id"]
    # [0] is 1024x1024, [1] is 400x400, [2] is 72x72
    if "food_images" in food_data:
        food.img_url = food_data["food_images"]["food_image"][1]["image_url"]


def prepare_recipe(ingredients_array=None, ingredients_amounts=None):
    """
    This function parameters are an array of n Food objects and n corresponding "amounts".
    Each Food object has its values adjusted based on the amount provided, for example
    if the starting base is relative to 100g and we request 50, then the values are halved.
    Only the main macros needed by the website are calculated, meaning calories, protein, carbs and fat.
    The new, updated Food objects are collected as a list inside a proper Recipe object (key "ingredients") and returned

    If the inputs aren't valid or of the same length, the we return a string explaining the problem.
    """
    recipe = Recipe()

    if ingredients_array is None or ingredients_amounts is None:
        return "At least one of the input data was None"
    if len(ingredients_array) != len(ingredients_amounts):
        return "The input parameters were not of the same length"

    for i in range(len(ingredients_array)):
        adjusted_food = adjust_ingredient(ingredients_array[i], ingredients_amounts[i])
        recipe.ingredients.append(adjusted_food)

        # Updates the total macros
        recipe.tot_protein += adjusted_food.protein
        recipe.tot_carbohydrate += adjusted_food.carbohydrate
        recipe.tot_fat += adjusted_food.fat
        recipe.tot_calories += adjusted_food.calories

    # The following values are sums of already rounded values but
    # operation with floats can produce artifacts, hence the final round is necessary
    recipe.tot_protein = round(recipe.tot_protein, 2)
    recipe.tot_calories = round(recipe.tot_calories, 2)
    recipe.tot_carbohydrate = round(recipe.tot_carbohydrate, 2)
    recipe.tot_fat = round(recipe.tot_fat, 2)

    return recipe


def prepare_plan(plan_raw=None, db=None):
    """
    plan_raw is expected to be the an array of dictionaries, i.e. the data "selected" from the database
    "plan_entries" table; db is the main database, it could be needed in case some plan entries are recipes made by the user

    The entire plan is prepared and returned, in particular this will be a dictionary with four keys: "breakfast",
    "lunch", "dinner", "snack" where the values are Recipe objects. Here each Recipe object can have as "ingredients"
    both Food or other Recipe objects. If any error occurs during the preparation, the function returns the relative string
    """
    plan = {
        "breakfast": Recipe(),
        "lunch": Recipe(),
        "dinner": Recipe(),
        "snack": Recipe(),
    }

    for entry in plan_raw:
        # Is this a simple food?
        if entry["id_food"] is not None:
            # Check if the food has already been fetched and stored in session, similarly to fetch_food_by_id
            if f"food_id_{entry['id_food']}" in session:
                food = session[f"food_id_{entry['id_food']}"]
            else:
                food = fetch_food_by_id(food_id=entry["id_food"])
            if isinstance(food, str):
                return food
            # Adjust the current food based on the relative amount indicated by the user
            prepared_entry = adjust_ingredient(food, entry["amount"])

            # The key simple_food is used to distinguish simple food from recipes
            plan[entry["meal"]].ingredients.append(
                {
                    "simple_food": True,
                    "food": prepared_entry,
                }
            )
            # Global macros are updated
            plan[entry["meal"]].tot_calories += prepared_entry.calories
            plan[entry["meal"]].tot_protein += prepared_entry.protein
            plan[entry["meal"]].tot_carbohydrate += prepared_entry.carbohydrate
            plan[entry["meal"]].tot_fat += prepared_entry.fat
        else:
            # We need both the ingredients and the recipe generic data
            list_ingredients = db.execute(
                "SELECT id_food, amount FROM recipes_entries WHERE id_recipe = ?",
                entry["id_recipe"],
            )
            recipe_data = db.execute(
                "SELECT name, total_servings FROM recipes WHERE id = ?",
                entry["id_recipe"],
            )
            # Fetch data from the API for each ingredient and prepare the list
            ingredients = []
            for ingredient in list_ingredients:
                if f"food_id_{ingredient['id_food']}" in session:
                    ingredients.append(session[f"food_id_{ingredient['id_food']}"])
                else:
                    ingredients.append(fetch_food_by_id(ingredient["id_food"]))
                    session[f"food_id_{ingredient['id_food']}"] = ingredients[-1]
            # We have to determine the amount of each ingredient in the recipe
            # entry["amount"] is how many servings of the recipe the user registered for this plan entry
            # float(ingredient["amount"]) is the amount of the current ingredient in the recipe
            # int(recipe_data[0]["total_servings"]) is the total amount of servings the user registered for the recipe
            amounts = [
                entry["amount"]
                * float(ingredient["amount"])
                / int(recipe_data[0]["total_servings"])
                for ingredient in list_ingredients
            ]
            # Weight the ingredients macros by the respective amounts
            # Return value is a Recipe object
            prepared_entry = prepare_recipe(ingredients, amounts)
            # "simple_food" is used to distinguish simple food from recipes
            # here we need to also save the id, name and amount of the recipe
            # because contrary to Food objects these information are not present inside Recipe objects
            plan[entry["meal"]].ingredients.append(
                {
                    "simple_food": False,
                    "id": entry["id_recipe"],
                    "name": recipe_data[0]["name"],
                    "amount": entry["amount"],
                    "food": prepared_entry,
                }
            )

            # Global macros are updated
            plan[entry["meal"]].tot_calories += prepared_entry.tot_calories
            plan[entry["meal"]].tot_protein += prepared_entry.tot_protein
            plan[entry["meal"]].tot_carbohydrate += prepared_entry.tot_carbohydrate
            plan[entry["meal"]].tot_fat += prepared_entry.tot_fat

    # Final rounding
    _extracted_from_prepare_plan(plan)
    return plan


def _extracted_from_prepare_plan(plan):
    """As always a final rounding is need to prevent strange artifacts"""
    plan["breakfast"].tot_calories = round(plan["breakfast"].tot_calories, 2)
    plan["breakfast"].tot_protein = round(plan["breakfast"].tot_protein, 2)
    plan["breakfast"].tot_carbohydrate = round(plan["breakfast"].tot_carbohydrate, 2)
    plan["breakfast"].tot_fat = round(plan["breakfast"].tot_fat, 2)
    plan["lunch"].tot_calories = round(plan["lunch"].tot_calories, 2)
    plan["lunch"].tot_protein = round(plan["lunch"].tot_protein, 2)
    plan["lunch"].tot_carbohydrate = round(plan["lunch"].tot_carbohydrate, 2)
    plan["lunch"].tot_fat = round(plan["lunch"].tot_fat, 2)
    plan["dinner"].tot_calories = round(plan["dinner"].tot_calories, 2)
    plan["dinner"].tot_protein = round(plan["dinner"].tot_protein, 2)
    plan["dinner"].tot_carbohydrate = round(plan["dinner"].tot_carbohydrate, 2)
    plan["dinner"].tot_fat = round(plan["dinner"].tot_fat, 2)
    plan["snack"].tot_calories = round(plan["snack"].tot_calories, 2)
    plan["snack"].tot_protein = round(plan["snack"].tot_protein, 2)
    plan["snack"].tot_carbohydrate = round(plan["snack"].tot_carbohydrate, 2)
    plan["snack"].tot_fat = round(plan["snack"].tot_fat, 2)


def adjust_ingredient(ingredient, amount):
    """
    Returns the adjusted food object ingredient based on the amount specified
    """
    # Creates the i-th food object in the recipe
    food = Food()
    # Save the name
    food.name = ingredient.name
    # Save the brand
    food.brand = ingredient.brand
    # Save the food_id
    food.food_id = ingredient.food_id
    # Save the new serving data
    food.measurement_description = ingredient.measurement_description
    food.number_of_units = amount
    food.serving_description = ingredient.serving_description
    multiplier = food.number_of_units / ingredient.number_of_units

    # Weight and save the main macros
    food.protein = round(ingredient.protein * multiplier, 2)
    food.carbohydrate = round(ingredient.carbohydrate * multiplier, 2)
    food.fat = round(ingredient.fat * multiplier, 2)
    food.calories = round(ingredient.calories * multiplier, 2)

    return food

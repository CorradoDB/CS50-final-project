# MyDiet
#### Video Demo:  [YouTube](https://www.youtube.com/watch?v=wrTJWmIdmug)

#### What this project is based on:

The project involves the use of Python3, Flask, Jinja, HTML, CSS, JavaScript, sqlite3 (through the module **cs50**)

#### Description:
Mydiet is a website where users can look up generic and branded food macronutrients and labels; create custom recipes; and finally combine everything inside their diet plans. The platform, in particular, aims to offer a clear view, through both tables and graphs, of all macro nutrients involved to better assist users in their planning and choices.

MyDiet is based on the database offered by the company [FatSecret](https://platform.fatsecret.com/) and the use of their API. As a disclaimer, this project needs an active premium account to make the necessary calls, and I was provided one for free after contacting their support team.  

The website has been programmed to be the most user-friendly possible, not only information are clearly displayed and delivered to the user, but also any possible error they should commit has been accounted for. Moreover, eventual exceptions raised by the inaccessibility of the database or the API are also taken into account

##

#### (Only relevant for GitHub) To use this repo you'll also need to provide these two files:
1. **keys.py** 

```
fs_consumer_key = "your consumer key"  
fs_consumer_secret = "your consumer secret"
```
2. **mydiet.db** which can be built through the provided .SQL file

##

FatSecret terms of use require that you not store any information provided by them besides the food IDs. To comply with this, I decided to fully structure my database so that it doesn't contain **any** hard record in regards to macronutrients, not even for the aggregation of food products or the various total amounts regarding any saved plan and meal.  
While this choice clearly implies more frequent API calls and therefore longer, even if very brief, delays for the user requests, it also offers a clear advantage: any changes made by the user are seamlessly and instantly reflected throughout the entire website because the macros displayed are always computed on the fly when required. Lowering the redundancy of data makes also the database safer in regards to its overall consistency. For example:

- Let's assume that the user decides to delete a recipe that was also part of a diet plan. By setting the rules of the relative foreign key as to *on delete cascade* and without hard saving any sort of intermediate or total macros value, nothing else is required beside the mandatory *DELETE* query. Note that by only storing the *amount* of a certain *something*, we can also avoid unnecessary API calls, data manipulation, and inspection of the database to determine what, how much, and where updates are needed. For example, updating a recipe's ingredient amount would potentially require fetching its macro, computing the difference, and updating all tables where the recipe is currently used.

We can further optimize the whole process by temporarily storing information inside *flask session*; for example, data relative to a specific food proved to be an obvious candidate. Not only that, we can also temporarily store the final computation of any recipe and plan data required by *Jinja* to render a specific HTML page, however in this case with all the necessary measures to assure that the data displayed remains always updated.

Some final clarifications before proceeding with the presentation of the three main features of the website:

#### **External resources**

- most of the **visual layouts** are based on *[bootstrap](https://getbootstrap.com/)* resources and adaptations of publicly available templates. For example, the food labels are adapted from [Chris Coyier codepen](https://codepen.io/chriscoyier/pen/ApavyZ)
- the structure of the **layout.html** template is mostly, apart from a few customizations, based on the one provided during **CS50 (2024) lectures**
- any displayed **graph** is built through javascript and uses [ChartJS libraries](https://www.chartjs.org/)
- **icons** are all part of the free packages offered by [flaticon](https://www.flaticon.com/)
- the font is **Montserrat** provided by **Google**
- additional Python packages are listed inside the *requirements.txt* file


#### **Food servings**

In this section I'll introduce how FatSecret handles the concept of *servings* and my thoughts on the subject 

- FatSecret, for each *food*, provides one **default** serving and **optionally** several others. Similarly, each serving is made out of its own dictionary where some keys are guaranteed, like calories and proteins, while many others aren't, like various vitamins. I opted to always display the data relative to the default serving as it is the one describing the real labels of each product, this is specifically relevant for the branded ones (in other words it's what we usually find on the back of the package). This wasn't my initial idea because if the user desires to compare two products, then having a mismatch in their serving sizes certainly complicates the process. Eventually, however, I would have been forced to discard all results that didn't come with a standardized serving size, and there would have been too many to make the tradeoff worth

- an additional problem regarding the *servings* specifications is that, the only guaranteed key to be always present where this information can be retrieved, doesn't respect a specific standard. In other words, often we can find the pattern **x y**, where **x** is the amount while **y** is the type of serving (examples: 1 cup, 100 grams, 2 oz), but it's not uncommon for the space to be missing, or for *x* to be a fraction (example: 1/2 cup). Ultimately, after many trials and errors where I simply observed what generated an exception, I came up with the most common patterns and decided to discard any result that uses something else. This is the only practical solution because it's impossible to scrape the entire database to determine any possible pattern, and in any case, for most of the queries only around 0.1% of the response doesn't pass the test, making the decision acceptable in my opinion

Why is it important to clearly define a measurement unit and the respective serving size? When we allow the user to add an entry to a generic table, they also have to specify the respective amount and, in my opinion, the only clean solution is that the latter must refer to the *single* measurement unit. Let's make an example to clarify what I mean: suppose that the displayed macros are relative to **2.5 oz**, the most user-friendly option is to ask the user "**how many oz do you want to add?**", and not "**how many 2.5 oz...***"; and without having already identified both *2.5* and *oz* this clearly wouldn't be possible


##
#### **Free Search:**

![free search](/static/FreeSearch.gif)
The first basic feature is to provide an independent, free search form. Here, the user can specify **name of the food** (required), **brand** (optional), and if the results have to be limited to be **branded** or **generic**.

It is important to specify here that *fatsecret* doesn't accept this sort of detailed search query; in fact, we can only submit a single text parameter, so this is how I dealt with the presented feature:
1. When a brand is specified, any result that doesn't have the selected brand inside the corresponding dictionary entry is promptly discarded. The same logic is applied for *only generic* and *only branded* options
2. Fatsecret, for each query, can return up to 50 results per call, and the initial offset can be specified through the appropriate parameter *page_number*. For example, if we request page *y* and *n* results, then the API would provide the top **n\*y** to **(n+1)\*y** matches. At the moment, the value *n* is hardcoded to **30** (the same for any other search of this kind), and the application requests up to 10 full pages until it can satisfy the user inputs. The philosophy behind this decision is that if the user didn't find what he wanted among the best 30 results, then he probably should be more specific in his next request

For visual clarity, the results are only initially displayed with their main data: calories, protein, carbohydrate (accompanied by sugar when possible), and fat relative to the default serving defined by FatSecret. The user can follow the specific hyperlinks to view on a different HTML page a complete nutrition label, a photo of the product (when available), and a graph where the main macro distribution can easily be observed.


##
##### **My Recipes**

![my recipes](/static/MyRecipes.png)
Being able to import personal recipes into diet plans is a necessary feature.  
Users can very easily create a new recipe by providing a name, and how many servings it's made of; later, by accessing a specific webpage, it's possible to update these data and to add, or remove, any ingredient from the composition of the recipe.  
As I previously explained, FatSecret doesn't accept complex search queries, hence why here the search form is but a simple input text. I find it also makes sense from a purely logical perspective because, contrary to *free search*, when defining a personal recipe the user should already know what ingredients he is looking for.  
Search results appear dynamically at the bottom of the page:

![my recipes query](/static/MyRecipes_Query.png)
where users can both be redirected, in a new tab, to each *food* description page or simply specify the amount the want to add to the recipe. 

##
##### **My Plans**

![my plans](/static/MyPlans.gif)

Being able to create personalized diet plans has been since the beginning what I envisioned to be the main feature of the website. The idea comes from a personal need that I had years ago where, and this is ultimately my take on it.  
For starters, I think plans should only track single days and not entire weeks to provide a more dynamic solution adaptable to non-fixed schedules. On the other hand, I decided to split every single day into four main *categories*: **breakfast**, **lunch**, **dinner**, and finally a generic **snack** where users can place anything that they plan to eat outside of the three main meals regardless of the specific day-time.  
The affinities with *my recipes* are a lot but here the visual data representation is much more present, for example instead of heaving a fifth table *total* I opted for showing each data inside specific, clean, bootstrap cards. The intention is to give the user the possibility to fully analyze a plan without having to necessarily look at as less complex tables as possible. 

Contrary to *my recipes*, here the search for a new *entry* is divided into multiple ones, and it takes place on a separate HTML page (each category has its own hyperlink). I find that the *visual complexity* of *my plans* is already enough and presenting the results in the page would have been too much.  
The only difference compared to *my recipes* is that here the form also allows the user to specify if the search should involve the public database or their personal recipes.

##

Final note: the app has been tested only inside VS Code, and through the debug mode with the following *launch.json*

```{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "Python Debugger: Flask",
			"type": "debugpy",
			"request": "launch",
			"module": "flask",
			"env": {
				"FLASK_APP": "app.py",
				"FLASK_DEBUG": "1"
			},
			"args": ["run", "--no-debugger", "--no-reload"],
			"jinja": true,
			"autoStartBrowser": false
		}
	]
}
```
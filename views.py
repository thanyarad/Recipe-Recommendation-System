from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import anthropic
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy.orm import load_only
import json
from app.models import db, User, RecipeRecord, RecipeString
import re

main = Blueprint("main", __name__)

client = anthropic.Anthropic()

RECIPES_PER_PAGE = 20


@main.route("/")
@login_required
def index():
    user = current_user
    page = 1

    recipes = (
        RecipeRecord.query.filter_by(user_id=user.id)
        .options(load_only(RecipeRecord.title, RecipeRecord.id))
        .order_by(RecipeRecord.id)
        .limit(RECIPES_PER_PAGE)
        .all()
    )
    recipe_dicts = [{"title": recipe.title, "id":recipe.id} for recipe in recipes]
    return render_template("index.html", recipes=recipe_dicts)


@main.route('/get-more-recipes')
def get_more_recipes():
    user = current_user
    page = int(request.args.get('page', 1))

    recipes = (
        RecipeRecord.query.filter_by(user_id=user.id)
        .options(load_only(RecipeRecord.title, RecipeRecord.id))
        .order_by(RecipeRecord.id)
        .offset((page - 1) * RECIPES_PER_PAGE)
        .limit(RECIPES_PER_PAGE)
        .all()
    )
    recipe_dicts = [{"title": recipe.title, "id":recipe.id} for recipe in recipes]
    return jsonify(recipe_dicts)


@main.route("/recipe_detail/<int:recipe_id>", methods=["GET", "POST"])
@login_required
def recipe_detail(recipe_id):
    recipe_data = RecipeRecord.query.get_or_404(recipe_id)
    dataset = {
        "title": recipe_data.title,
        "ingredients": recipe_data.ingredients,
        "description": recipe_data.description.replace('\\n', '\n').replace('\n', '<br>').replace('\\', ''),
        "youtube_link": recipe_data.youtube_link,
    }
    return render_template(
        "recipe_detail.html",
        recipe=dataset,
    )




@main.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]

        user = User(full_name=full_name, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        flash("Signup successful! Please log in.", "success")
    return render_template(
        "signup.html",
    )


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


@main.route("/generate-new", methods=["GET", "POST"])
@login_required
def generate_new():
    if request.method == "POST":
        user = current_user
        data = request.form["ingredients"].split(',')
        response = claude_call(ingredients=data)
        res_with_br = response.replace("\n", "<br>")
        res_string = RecipeString(dataset=response)
        db.session.add(res_string)
        db.session.commit()
        output_string = response.strip()

        # Use a more robust regex to capture the entire description, including newlines
        output_string = re.sub(r'("description":)(".*?")',
                               lambda m: m.group(1) + json.dumps(m.group(2)[1:-1]),
                               output_string, flags=re.DOTALL)

        recipe_dict = json.loads(output_string)
        new_recipe = RecipeRecord(
            title=recipe_dict["title"],
            user_id=user.id,
            description=recipe_dict["description"],
            ingredients=recipe_dict["ingredients"]
        )
        db.session.add(new_recipe)
        db.session.commit()

        return redirect(url_for('main.recipe_detail', recipe_id=new_recipe.id))

    return render_template("recipe.html", ingredients=[])



prompt_sys = """
You are Intelligent Recipe Generator. Given the Ingredients list, generate one recipe as per the ingredients.

Output in json format
{
"title":"",
"ingredients":["", ""]
"description":"this should include `steps`"
}

Note: Output should be JSON only
"""


def claude_call(ingredients=[]):
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.8,
        system=prompt_sys,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": str(ingredients)}]}
        ],
    )
    return message.content[0].text

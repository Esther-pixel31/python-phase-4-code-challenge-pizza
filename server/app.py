#!/usr/bin/env python3

from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_restful import Api
from models import db, Restaurant, RestaurantPizza, Pizza
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>", 200


@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([r.to_dict(rules=("-pizzas", "-restaurant_pizzas")) for r in restaurants]), 200


@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    return jsonify(restaurant.to_dict(rules=())), 200


@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    db.session.delete(restaurant)
    db.session.commit()
    return '', 204


@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([p.to_dict(rules=("-restaurant_pizzas", "-restaurants")) for p in pizzas]), 200


@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()

    if not data:
        return jsonify({"errors": ["Invalid JSON body"]}), 400

    pizza = db.session.get(Pizza, data.get("pizza_id"))
    restaurant = db.session.get(Restaurant, data.get("restaurant_id"))

    if not pizza or not restaurant:
        return jsonify({"errors": ["Pizza or Restaurant not found"]}), 404

    try:
        new_rp = RestaurantPizza(
            price=data["price"],
            pizza_id=pizza.id,
            restaurant_id=restaurant.id,
        )
        db.session.add(new_rp)
        db.session.commit()

        return jsonify({
            "id": new_rp.id,
            "price": new_rp.price,
            "pizza_id": new_rp.pizza_id,
            "restaurant_id": new_rp.restaurant_id,
            "pizza": pizza.to_dict(rules=("-restaurant_pizzas", "-restaurants")),
            "restaurant": restaurant.to_dict(rules=("-restaurant_pizzas", "-pizzas"))
        }), 201

    except ValueError:
        db.session.rollback()
        return jsonify({"errors": ["validation errors"]}), 400

    except Exception:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({"errors": ["An unexpected error occurred."]}), 500


if __name__ == "__main__":
    app.run(port=5555, debug=True)

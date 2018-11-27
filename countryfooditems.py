from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Country, Base, FoodItem, User

engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Add countries and food items
User1 = User(name="John Doe", email="johndoe@johndoe.com",
             picture='')
session.add(User1)
session.commit()


russia = Country(user_id=1, name="Russia")

session.add(russia)
session.commit()

foodItem1 = FoodItem(name="Borsch",
                     description="Beat, veggie, and sometimes"
                     " tomato soup served with sourcream",
                     country=russia)

session.add(foodItem1)
session.commit()


foodItem2 = FoodItem(user_id=1, name="Pelmeni",
                     description="Boiled dough dumplings"
                     " with chicken or beef",
                     country=russia)

session.add(foodItem2)
session.commit()

italy = Country(user_id=1, name="Italy")

session.add(italy)
session.commit()

foodItem1 = FoodItem(user_id=1, name="Speghetti",
                     description="Long, thin pasta usually"
                     " served with cheese and meat",
                     country=italy)

session.add(foodItem1)
session.commit()


foodItem2 = FoodItem(user_id=1, name="Pizza",
                     description="Baked dough within toppings"
                     " such as tomato and meat and cheese on top",
                     country=italy)

session.add(foodItem2)
session.commit()

mexico = Country(user_id=1, name="Mexico")

session.add(mexico)
session.commit()

foodItem1 = FoodItem(user_id=1, name="Tacos",
                     description="Tortillas folded"
                     " with meat, greens, and salsa",
                     country=mexico)

session.add(foodItem1)
session.commit()


foodItem2 = FoodItem(user_id=1, name="Burrito",
                     description="Veggies, rice, meat,"
                     " and beans wrapped in a tortilla",
                     country=mexico)

session.add(foodItem2)
session.commit()

canada = Country(user_id=1, name="Canada")

session.add(canada)
session.commit()

foodItem1 = FoodItem(user_id=1, name="Poutine",
                     description="Fries with gravy"
                     " and cheese curds",
                     country=canada)

session.add(foodItem1)
session.commit()


foodItem2 = FoodItem(user_id=1, name="Beavertails",
                     description="Deep-fried dough"
                     " covered in caramel and chocolate",
                     country=canada)

session.add(foodItem2)
session.commit()

print "added food items!"

BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL UNIQUE,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "plans_entries" (
	"id"	INTEGER NOT NULL UNIQUE,
	"id_plan"	INTEGER NOT NULL,
	"id_food"	INTEGER,
	"id_recipe"	INTEGER,
	"meal"	TEXT NOT NULL,
	"amount"	REAL NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id_plan") REFERENCES "plans"("id") ON DELETE CASCADE,
	FOREIGN KEY("id_recipe") REFERENCES "recipes"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "recipes_entries" (
	"id"	INTEGER NOT NULL UNIQUE,
	"id_food"	INTEGER NOT NULL,
	"id_recipe"	INTEGER NOT NULL,
	"amount"	REAL NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id_recipe") REFERENCES "recipes"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "recipes" (
	"id"	INTEGER NOT NULL UNIQUE,
	"user_id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"total_servings"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "plans" (
	"id"	INTEGER NOT NULL UNIQUE,
	"user_id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"last_edited"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "recipes_entries: id_recipe" ON "recipes_entries" (
	"id_recipe"
);
CREATE INDEX IF NOT EXISTS "plans: users_id" ON "plans" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "plans_entries: id_plan" ON "plans_entries" (
	"id_plan"
);
CREATE INDEX IF NOT EXISTS "plans_entries: id_plan, id_food, meal" ON "plans_entries" (
	"id_plan",
	"id_food",
	"meal"
);
CREATE INDEX IF NOT EXISTS "plans_entries: id_plan, id_recipe, meal" ON "plans_entries" (
	"id_plan",
	"id_recipe",
	"meal"
);
CREATE INDEX IF NOT EXISTS "recepes: users_id" ON "recipes" (
	"user_id"
);
CREATE INDEX IF NOT EXISTS "recipes_entries: id_food, id_recipe" ON "recipes_entries" (
	"id_food",
	"id_recipe"
);
CREATE INDEX IF NOT EXISTS "users: usernames" ON "users" (
	"username"
);
COMMIT;

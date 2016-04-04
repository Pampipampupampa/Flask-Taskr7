# -*- coding:Utf8 -*-


from project import db, bcrypt
from project.models import User

########################
#    Main Program :    #
########################


if __name__ == '__main__':
    # Initialize database schema (all tables, views, triggers)
    db.create_all()

    # Add administrateur user
    new_user = User(name="administrateur", email="admin@monMail.com",
                    password=bcrypt.generate_password_hash("administrateur"),
                    role="admin")
    db.session.add(new_user)

    # Commit changes
    db.session.commit()

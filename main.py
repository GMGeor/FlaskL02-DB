from decouple import config  # pip name is python-decouple
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_migrate import Migrate

app = Flask(__name__)

db_user = config('DB_USER')
db_password = config('DB_PASSWORD')
db_port = config('DB_PORT')
db_name = config('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@localhost:{db_port}/{db_name}'

db = SQLAlchemy(app)
api = Api(app)
migrate = Migrate(app,
                  db)  # now with migrate we can work from the terminal, it is not used in the code. don't forgot  set FLASK_APP=./main.py

association_table = db.Table(
    'association',
    db.metadata,
    db.Column("book_pk", db.Integer, db.ForeignKey("books.pk"), primary_key=True),
    db.Column("reader_pk", db.Integer, db.ForeignKey("readers.pk"), primary_key=True),
)


class BookModel(db.Model):
    __tablename__ = 'books'

    pk = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    # reader_pk = db.Column(db.Integer, db.ForeignKey("readers.pk"))
    # reader = db.relationship("ReaderModel")  # !!! flask-alchemy alows instead of creating joins on the fly to get in memory the reader(otherwise we can see only the reder_pk)
    reader = db.relationship("ReaderModel", secondary=association_table, backref="book")

    def __repr__(self):
        return f"<{self.pk}> {self.title} from {self.author}"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ReaderModel(db.Model):
    __tablename__ = 'readers'

    pk = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    books = db.relationship("BookModel", secondary=association_table)
    # books = db.relationship("BookModel", backref="book", lazy='dynamic')  # similarly to reader now we can see books of the reader!!!
    # lazy='dynamic' to execute only when called(ReaderModel.query.all()[0].books .books calls it), better performance

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Books(Resource):

    def get(self):
        books = BookModel.query.all()
        books_data = [b.as_dict() for b in books]
        return {"books": books_data}

    def post(self):
        data = request.get_json()
        new_book = BookModel(**data)
        db.session.add(new_book)
        db.session.commit()
        return new_book.as_dict()


class Reader(Resource):
    def get(self, reader_pk):
        reader = ReaderModel.query.filter_by(pk=reader_pk).first()
        books = BookModel.query.filter_by(reader_pk=reader_pk)
        # books = association_table.`
        return {"data": [book.as_dict() for book in reader.books]}

    # def post(self):
    #     data = request.get_json()
    #     new_reader = ReaderModel(**data)
    #     db.session.add(new_reader)
    #     db.session.commit()
    #     return new_reader.as_dict()


api.add_resource(Books, "/")
api.add_resource(Reader, "/readers/<int:reader_pk>/books")

if __name__ == "__main__":
    app.run(debug=True)

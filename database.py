from peewee import *
import hashlib
import hmac
import datetime
import uuid

from Crypto import Random
from Crypto.Cipher import AES

DB_PATH = 'blog.sqlite'  # in normal deployment, should be abs path

db = SqliteDatabase(DB_PATH)

class MyModel(Model):
    class Meta:
        database = db

class Author(MyModel):
    slug = CharField(unique=True)
    name = TextField()
    description = TextField()
    is_editor = BooleanField()

    password = BlobField()
    salt = BlobField()

    def set_password(self, password):
        self.salt = Random.new().read(AES.block_size)
        self.password = hashlib.scrypt(bytes(password, 'utf-8'), salt=self.salt, n=2**12, r=8, p=8)
        if not self.check_password(password):
            raise ValueError('failed to trial authenticate')
        self.save()

    def check_password(self, password):
        password = bytes(password, 'utf-8')
        test_password = hashlib.scrypt(password, salt=self.salt, n=2**12, r=8, p=8)
        return hmac.compare_digest(self.password, test_password)


# AES code from https://stackoverflow.com/a/20868265

def pad(s):
    return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

def encrypt(message, key):
    message = pad(message)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(message)

def decrypt(ciphertext, key):
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[AES.block_size:])
    return plaintext.rstrip(b"\0")

class Article(MyModel):
    slug = CharField(unique=True)
    title = TextField()
    subtitle = TextField(null=True)
    date = DateTimeField(default=datetime.datetime.now)
    author = ForeignKeyField(Author, backref='articles')
    listed = BooleanField()
    version = UUIDField(default=uuid.uuid4)

    encrypted = BooleanField()
    salt = BlobField(null=True)
    n_exp = IntegerField(null=True)  # n=2**n_exp
    r = IntegerField(null=True)
    p = IntegerField(null=True)
    magic_prefix = BlobField(null=True)
    magic_suffix = BlobField(null=True)

    content = BlobField()

    def decrypt(self, password):
        if not self.encrypted:
            return self.content
        password = bytes(password, 'utf-8')
        key = hashlib.scrypt(password, salt=self.salt, n=2**self.n_exp, r=self.r, p=self.p, dklen=32)
        plaintext = decrypt(self.content, key)
        if plaintext.startswith(self.magic_prefix or b'') and plaintext.endswith(self.magic_suffix or b''):
            return plaintext[len(self.magic_prefix) : -len(self.magic_suffix)]
        else:
            raise ValueError('decryption failed, check key')

    def decrypt_in_place(self, password):
        plaintext = self.decrypt(password)
        self.encrypted = False
        self.salt = None
        self.n_exp = None
        self.r = None
        self.p = None
        self.magic_prefix = None
        self.magic_suffix = None
        self.content = plaintext
        self.save()

    def encrypt_in_place(self, password, salt=None, n_exp=10, r=8, p=1, magic_prefix=b'Article content: \n\n', magic_suffix=b'\n\n=== Article content ends here'):
        salt = salt or Random.new().read(64)
        key = hashlib.scrypt(bytes(password, 'utf-8'), salt=salt, n=2**n_exp, r=r, p=p, dklen=32)
        plaintext = self.content
        ciphertext = encrypt(plaintext, key)

        self.encrypted = True
        self.content = ciphertext
        self.salt = salt
        self.n_exp = n_exp
        self.r = r
        self.p = p
        self.magic_prefix = magic_prefix
        self.magic_suffix = magic_suffix

        # before saving, confirm that we can decrypt it
        # (should never be an issue)
        if plaintext != self.decrypt(password):
            raise ValueError('Failed to trial decrypt content')
        self.save()


class Tag(MyModel):
    slug = CharField(unique=True)

class ArticleTag(MyModel):
    article = ForeignKeyField(Article, backref='tags')
    tag = ForeignKeyField(Tag, backref='articles')


db.connect()
db.create_tables([Author, Article, Tag, ArticleTag])
db.close()

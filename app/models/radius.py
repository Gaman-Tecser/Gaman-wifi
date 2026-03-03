"""Modelos que mapean las tablas existentes de FreeRADIUS. NO gestionadas por Alembic."""
from app.extensions import db


class Radcheck(db.Model):
    __tablename__ = "radcheck"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, default="")
    attribute = db.Column(db.String(64), nullable=False, default="")
    op = db.Column(db.String(2), nullable=False, default="==")
    value = db.Column(db.String(253), nullable=False, default="")


class Radreply(db.Model):
    __tablename__ = "radreply"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, default="")
    attribute = db.Column(db.String(64), nullable=False, default="")
    op = db.Column(db.String(2), nullable=False, default="=")
    value = db.Column(db.String(253), nullable=False, default="")


class Radusergroup(db.Model):
    __tablename__ = "radusergroup"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, default="")
    groupname = db.Column(db.String(64), nullable=False, default="")
    priority = db.Column(db.Integer, nullable=False, default=1)


class Radgroupcheck(db.Model):
    __tablename__ = "radgroupcheck"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(64), nullable=False, default="")
    attribute = db.Column(db.String(64), nullable=False, default="")
    op = db.Column(db.String(2), nullable=False, default="==")
    value = db.Column(db.String(253), nullable=False, default="")


class Radgroupreply(db.Model):
    __tablename__ = "radgroupreply"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(64), nullable=False, default="")
    attribute = db.Column(db.String(64), nullable=False, default="")
    op = db.Column(db.String(2), nullable=False, default="=")
    value = db.Column(db.String(253), nullable=False, default="")


class Nas(db.Model):
    __tablename__ = "nas"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    nasname = db.Column(db.Text, nullable=False)
    shortname = db.Column(db.String(32))
    type = db.Column(db.String(30), default="other")
    ports = db.Column(db.Integer)
    secret = db.Column(db.String(60), nullable=False, default="secret")
    server = db.Column(db.String(64))
    community = db.Column(db.String(50))
    description = db.Column(db.String(200), default="RADIUS Client")


class Radacct(db.Model):
    __tablename__ = "radacct"
    __table_args__ = {"extend_existing": True}

    radacctid = db.Column(db.BigInteger, primary_key=True)
    acctsessionid = db.Column(db.String(64), nullable=False, default="")
    acctuniqueid = db.Column(db.String(32), nullable=False, unique=True)
    username = db.Column(db.String(64), nullable=False, default="")
    realm = db.Column(db.String(64), default="")
    nasipaddress = db.Column(db.Text, nullable=False, default="")
    nasportid = db.Column(db.String(15))
    nasporttype = db.Column(db.String(32))
    acctstarttime = db.Column(db.DateTime)
    acctupdatetime = db.Column(db.DateTime)
    acctstoptime = db.Column(db.DateTime)
    acctinterval = db.Column(db.BigInteger)
    acctsessiontime = db.Column(db.BigInteger)
    acctauthentic = db.Column(db.String(32))
    connectinfo_start = db.Column(db.String(50))
    connectinfo_stop = db.Column(db.String(50))
    acctinputoctets = db.Column(db.BigInteger)
    acctoutputoctets = db.Column(db.BigInteger)
    calledstationid = db.Column(db.String(50), nullable=False, default="")
    callingstationid = db.Column(db.String(50), nullable=False, default="")
    acctterminatecause = db.Column(db.String(32), nullable=False, default="")
    servicetype = db.Column(db.String(32))
    framedprotocol = db.Column(db.String(32))
    framedipaddress = db.Column(db.Text, nullable=False, default="")
    framedipv6address = db.Column(db.Text, nullable=False, default="")
    framedipv6prefix = db.Column(db.Text, nullable=False, default="")
    framedinterfaceid = db.Column(db.String(44), nullable=False, default="")
    delegatedipv6prefix = db.Column(db.Text, nullable=False, default="")
    class_ = db.Column("class", db.Text, default="")


class Radpostauth(db.Model):
    __tablename__ = "radpostauth"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    pass_ = db.Column("pass", db.String(64), nullable=False, default="")
    reply = db.Column(db.String(32))
    authdate = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    class_ = db.Column("class", db.Text, default="")

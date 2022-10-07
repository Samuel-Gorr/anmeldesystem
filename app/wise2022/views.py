# coding=utf-8
from . import reg_blueprint
from flask import render_template, session, redirect, url_for, flash, current_app
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    SelectMultipleField,
    SubmitField,
    BooleanField,
    validators,
    IntegerField,
)
from wtforms.fields import DateField
from wtforms.widgets import TextArea
from wtforms.widgets import NumberInput 
from app.oauth_client import oauth_remoteapp, getOAuthToken
import json
from datetime import datetime, time, timezone
import pytz


## Merch Auswahloptionen definieren

T_SHIRT_CHOICES = [
    ("keins", "Nein, ich möchte keins"),
    ("xxl", "XXL"),
    ("xl", "XL"),
    ("l", "L"),
    ("m", "M"),
    ("s", "S"),
    ("xs", "XS"),
]
T_SHIRT_SCHNITT_CHOICES = [
    ("keins", "Nein, ich möchte wirklich keins"),
    ("mens-fit", "Mens-Fit"),
    ("ladies-fit", "Ladies-Fit"),
]
# Gerne auskommentierte Sachen wieder reinnehmen, falls ihr motivierter wart mit der Merchbeschaffung als wir

# HOODIE_CHOICES = [
#        ('keins', 'Nein, ich möchte keinen'),
#        ('fitted_xxl', 'XXL fitted'),
#       ('fitted_xl', 'XL fitted'),
#       ('fitted_l', 'L fitted'),
#        ('fitted_m', 'M fitted'),
#        ('fitted_s', 'S fitted'),
#        ('fitted_xs', 'XS fitted'),
#        ('5xl', '5XL'),
#        ('4xl', '4XL'),
#        ('3xl', '3XL'),
#        ('xxl', 'XXL'),
#        ('xl', 'XL'),
#        ('l', 'L'),
#        ('m', 'M'),
#        ('s', 'S'),
#        ('xs', 'XS'),
#        ]


# MERCH_COLORS = [
#        ('navy','Navy'),
#        ('grau','Dunkelgrau'),
#        ('schwarz','Schwarz'),
#        ]


class ImmatrikulationsValidator(object):
    def __init__(self, following=None):
        self.following = following

    def __call__(self, form, field):
        if field.data != "ja" and field.data != "n.i.":
            raise validators.ValidationError(
                "Bitte gib an, dass du deine Immatrikulationsbescheinigung mitbringen wirst oder, dass du keine hast."
            )


class ImmatrikulationsValidator2(object):
    def __init__(self, following=None):
        self.following = following

    def __call__(self, form, field):
        if field.data != "nein" and field.data != "n.i.":
            raise validators.ValidationError(
                "Bitte gib an, dass du deine Immatrikulationsbescheinigung nicht vergessen wirst."
            )


class ExkursionenValidator(object):
    def __init__(self, following=None):
        self.following = following

    def __call__(self, form, field):
        if field.data == "keine":
            for follower in self.following:
                if follower.data != "keine":
                    raise validators.ValidationError(
                        "Die folgenden Exkursionen sollten auch auf "
                        '"Keine Exkursion" stehen, alles anderes ist '
                        "nicht sinnvoll ;)."
                    )
        elif field.data != "egal":
            for follower in self.following:
                if follower.data == field.data:
                    raise validators.ValidationError(
                        "Selbe Exkursion mehrfach als Wunsch ausgewählt"
                    )


class RegistrationForm(FlaskForm):
    @classmethod
    def append_field(cls, name, field):
        setattr(cls, name, field)
        return cls

    def __init__(self, **kwargs):
        super(RegistrationForm, self).__init__(**kwargs)
        self.immatrikulationsbescheinigung.validators = [
            ImmatrikulationsValidator(self.immatrikulationsbescheinigung)
        ]
        self.immatrikulationsbescheinigung2.validators = [
            ImmatrikulationsValidator2(self.immatrikulationsbescheinigung2)
        ]

    #### Allgemein #####
    uni = SelectField("Uni", choices=[], coerce=str)
    spitzname = StringField("Spitzname")
    # Die Abfrage, ob Immabescheinigung mitgebracht wird geschieht später an zwei Orten. Einmal im allgemeinen Teil und die erinnerung am Ende der Anmeldung
    immatrikulationsbescheinigung = SelectField(
        "Bringst du deine Immatrikulationsbescheinigung mit?",
        choices=[
            ("invalid", "---"),
            (
                "ja",
                "Ich bin an einer Hochschule immatrikuliert und bringe eine gültige Bescheinigung darüber mit.",
            ),
            (
                "nein",
                "Ich bin an einer Hochschule immatrikuliert und bringe keine gültige Bescheinigung darüber mit.",
            ),
            (
                "n.i.",
                "Ich bin an keiner Hochschule immatrikuliert und bringe keine gültige Bescheinigung darüber mit.",
            ),
        ],
    )
    immatrikulationsbescheinigung2 = SelectField(
        "Wirst du deine Immatrikulationsbescheinigung vergessen?",
        choices=[
            ("invalid", "---"),
            ("ja", "Ja."),
            ("nein", "Nein."),
            ("n.i.", "Ich habe keine."),
        ],
    )

    musikwunsch = StringField("Musikwunsch")

    ###### Essen ######

    essen = SelectField(
        "Essen",
        choices=[
            ("omnivor", "Omnivor"),
            ("vegetarisch", "Vegetarisch"),
            ("vegan", "Vegan"),
        ],
    )
    allergien = StringField("Allergien oder sonstige Essensformen z.B. koscher")
    heissgetraenk = SelectField(
        "Kaffee oder Tee?",
        choices=[
            #        ('egal', 'Egal'),
            ("kaffee", "Kaffee"),
            ("tee", "Tee"),
            ("unparteiisch", "Unparteiisches Alpaka"),
        ],
    )
    alkohol = SelectField(
        "Trinkst du Alkohol",
        choices=[
            ("ja", "Ja"),
            ("nein", "Nein"),
            ("ka", "Keine Angabe"),
        ],
    )


    #### Merch #####

    tshirt = SelectField("T-Shirt", choices=T_SHIRT_CHOICES)
    nrtshirt = IntegerField(
        "Anzahl T-Shirts", [validators.optional()], widget=NumberInput(min=0, max=10)
    )
    tasse = BooleanField(
         "Ich möchte eine Tagungstasse haben."
    )
    nottasche = BooleanField(
         "Ich möchte KEINE Tagungstasche haben (den Inhalt kriegst du trotzdem)."
    )
    

    #### Reiseinfos ####

    anreise_witz = SelectField(
        "Verkehrsmittel deiner Wahl",
        choices=[
            ("bus", "Fernbus"),
            ("bahn", "Zug"),
            ("auto", "Auto"),
            ("zeitmaschine", "Zeitmaschine"),
            ("flohpulver", "Flohpulver"),
            ("fahrrad", "Fahrrad"),
            ("badeente", "Badeente"),
        ],
    )
    anreise_zeit = SelectField(
        "Anreise vorraussichtlich:",
        choices=[
            ("frueher", "Ich komme früher und helfe gerne beim Aufbau."),
            ("fr014", "Freitag vor 14 Uhr"),
            ("fr114", "Freitag nach 14 Uhr"),
            ("ende", "Samstag"),
        ],
    )

    #   excar = BooleanField('Ich reise mit einem Auto an und bin bereit, auf Exkursionen Zapfika mitzunehmen.')

    abreise_zeit = SelectField(
        "Abreise vorraussichtlich:",
        choices=[
            ("vorso", "Vor Sonntag"),
            ("di014", "Sonntag vor 14 Uhr"),
            ("di114", "Sonntag nach 14 Uhr"),
        ],
    )

    ##### Standorte ######

    barrierefreiheit = BooleanField(
        "Ich habe spezifische Ansprüche an Barrierefreiheit."
    )

    eduroam = BooleanField(
        "Ich habe Eduroam (Internet-Zugangsdienst)."
    )


    notbinarytoiletten = BooleanField(
                "Ich möchte während der ZaPF die Möglichkeit haben nicht binär-geschlechtliche Toiletten zu verwenden"
            )
    schlafen = SelectField(
        "Wie möchtest du geweckt werden?",
        choices=[
            ("laut", "laut"),
            ("elaut", "eher laut"),
            ("egal", "egal"),
            ("eleise", "eher leise"),
            ("leise", "leise"),
        ],
    )
    
    couchsurfing = BooleanField(
                "Ich würde auch eine Schlafmöglichkeit via Couchsurfing nutzen.",
            )
        
    privatunterkunft = BooleanField(
                "Ich habe eine private Schlafmöglichkeit.",
            )    

    foerderung = BooleanField("Ja")

    hygiene = BooleanField("Ja")

    #### Sonstiges ####
    zaepfchen = SelectField(
        "Kommst du zum ersten mal zu einer ZaPF?",
        choices=[
            ("ja", "Ja"),
            ("jaund", "Ja und ich hätte gerne einen ZaPF-Mentor."),
            ("nein", "Nein"),
        ],
    )
    mentor = BooleanField(
        "Ich möchte ZaPF-Mentorikon werden und erkläre mich damit einverstanden, dass meine E-Mail-Adresse an ein Zäpfchen weitergegeben wird."
    )
    foto = BooleanField(
        "Ich bin damit einverstanden, dass Fotos von mir gemacht werden. Diese werden evtl im Tagungsreader genutzt. und nicht für kommerzielle Zwecke verwendet."
    )
    akleitung = BooleanField(
         "Ich möchte einen AK auf der ZaPF leiten."
    )
    redeleitung = BooleanField(
         "Ich möchte bei der Redeleitung der Plena mit machen."
    )
    gremiumwahl = BooleanField(
         "Ich möchte mich in ein Gremium wählen lassen (https://zapf.wiki/Übersicht#Gremien_der_ZaPF)."
    )
    alter = SelectField(
        "Ich bin zum Zeitpunkt der ZaPF:",
        choices=[
            ("u16", "JÜNGER als 16 Jahre"),
            ("u18", "JÜNGER als 18 Jahre"),
            ("18-26", "ZWISCHEN 18 und 26 Jahren"),
            ("a26", "ÄLTER als 26 Jahre"),
        ],
    )
    kommentar = StringField(
        "Möchtest Du uns sonst etwas mitteilen?",
        #   gremien = BoolanField('Ich bin Mitglied in StAPF, TOPF, KommGrem, oder ZaPF-e.V-Vorstand und moechte mich über das Gremienkontingent anmelden.')
        widget=TextArea(),
    )
    submit = SubmitField()
    vertrauensperson = SelectField(
        'Wärst Du bereit, dich als Vertrauensperson aufzustellen? (Du weißt nicht was das ist? Gib bitte "Nein" an!)',
        choices=[
            ("nein", "Nein"),
            ("ja", "Ja"),
        ],
    )
    protokoll = SelectField(
        "Wärst Du bereit bei den Plenen Protokoll zu schreiben?",
        choices=[
            ("nein", "Nein"),
            ("ja", "Ja"),
        ],
    )
    ##### Datenschutz ######

    datenschutz = BooleanField("Ja", [validators.InputRequired()])


@reg_blueprint.route("/", methods=["GET", "POST"])
def index():
    registration_open = (
        datetime.now(pytz.utc) <= current_app.config["REGISTRATION_SOFT_CLOSE"]
    ) or current_app.config["REGISTRATION_FORCE_OPEN"]
    priorities_open = (
        datetime.now(pytz.utc) <= current_app.config["REGISTRATION_HARD_CLOSE"]
    ) or current_app.config["REGISTRATION_FORCE_PRIORITIES_OPEN"]
    is_admin = (
        "me" in session
        and session["me"]["username"] in current_app.config["ADMIN_USERS"]
    )

    if not is_admin and not priorities_open:
        return render_template("registration_closed.html")

    if "me" not in session:
        return render_template(
            "landing.html",
            registration_open=registration_open,
            priorities_open=priorities_open,
        )

    if not getOAuthToken():
        flash(
            "Die Sitzung war abgelaufen, eventuell musst du deine Daten nochmal eingeben, falls sie noch nicht gespeichert waren.",
            "warning",
        )
        return redirect(url_for("oauth_client.login"))

    Form = RegistrationForm

    defaults = {}
    confirmed = None
    req = oauth_remoteapp.get("registration")
    if req._resp.code == 200:
        defaults = json.loads(req.data["data"])
        if "geburtsdatum" in defaults and defaults["geburtsdatum"]:
            defaults["geburtsdatum"] = datetime.strptime(
                defaults["geburtsdatum"], "%Y-%m-%d"
            )
        confirmed = req.data["confirmed"]
    else:
        if not is_admin and not registration_open:
            return render_template("registration_closed.html")

    # Formular erstellen
    form = Form(**defaults)

    # Die Liste der Unis holen
    unis = oauth_remoteapp.get("unis")
    if unis._resp.code == 500:
        raise
    if unis._resp.code != 200:
        return redirect(url_for("oauth_client.login"))
    form.uni.choices = sorted(unis.data.items(), key=lambda uniEntry: int(uniEntry[0]))

    # Daten speichern
    if form.submit.data and form.validate_on_submit():
        req = oauth_remoteapp.post(
            "registration",
            format="json",
            data=dict(
                uni_id=form.uni.data,
                data={
                    k: v
                    for k, v in form.data.items()
                    if k not in ["csrf_token", "submit"]
                },
            ),
        )
        if req._resp.code == 200 and req.data.decode("utf-8") == "OK":
            flash("Deine Anmeldedaten wurden erfolgreich gespeichert", "info")
        else:
            flash("Deine Anmeldendaten konnten nicht gespeichert werden.", "error")
        return redirect("/")

    return render_template("index.html", form=form, confirmed=confirmed)


@reg_blueprint.route("/admin/wise21/<string:username>", methods=["GET", "POST"])
def adminEdit(username):
    if "me" not in session:
        return redirect("/")

    is_admin = (
        "me" in session
        and session["me"]["username"] in current_app.config["ADMIN_USERS"]
    )
    if not is_admin:
        abort(403)

    if not getOAuthToken():
        flash(
            "Die Sitzung war abgelaufen, eventuell musst du deine Daten nochmal eingeben, falls sie noch nicht gespeichert waren.",
            "warning",
        )
        return redirect(url_for("oauth_client.login"))

    Form = RegistrationForm

    defaults = {}
    confirmed = None
    req = oauth_remoteapp.get("registration", data={"username": username})
    if req._resp.code == 200:
        defaults = json.loads(req.data["data"])
        if "geburtsdatum" in defaults and defaults["geburtsdatum"]:
            defaults["geburtsdatum"] = datetime.strptime(
                defaults["geburtsdatum"], "%Y-%m-%d"
            )
        confirmed = req.data["confirmed"]
    elif req._resp.code == 409:
        flash("Username is unknown", "error")
        return redirect("/")

    # Formular erstellen
    form = Form(**defaults)

    # Die Liste der Unis holen
    unis = oauth_remoteapp.get("unis")
    if unis._resp.code != 200:
        return redirect(url_for("oauth_client.login"))
    form.uni.choices = sorted(unis.data.items(), key=lambda uniEntry: int(uniEntry[0]))

    # Daten speichern
    if form.submit.data and form.validate_on_submit():
        req = oauth_remoteapp.post(
            "registration",
            format="json",
            data=dict(
                username=username,
                uni_id=form.uni.data,
                data={
                    k: v
                    for k, v in form.data.items()
                    if k not in ["csrf_token", "submit"]
                },
            ),
        )
        if req._resp.code == 200 and req.data.decode("utf-8") == "OK":
            flash("Deine Anmeldedaten wurden erfolgreich gespeichert", "info")
        else:
            flash("Deine Anmeldendaten konnten nicht gespeichert werden.", "error")
        return redirect(url_for("sommer20.adminEdit", username=username))

    return render_template("index.html", form=form, confirmed=confirmed)

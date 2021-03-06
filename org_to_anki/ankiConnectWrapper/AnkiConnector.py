from .AnkiConnectorUtils import AnkiConnectorUtils
from ..ankiClasses import AnkiQuestion
from ..ankiClasses.AnkiDeck import AnkiDeck
from .. import config


class AnkiConnector:

    def __init__(
            self,
            url=config.defaultAnkiConnectAddress,
            defaultDeck=config.defaultDeck):
        self.url = url  # TODO remove
        self.defaultDeck = defaultDeck
        self.currentDecks = []
        self.connector = AnkiConnectorUtils(self.url)

    def uploadNewDeck(self, deck: AnkiDeck):

        if self.connector.testConnection() is not True:
            print(
                "Failed to connect to Anki Connect. \
                Ensure Anki is open and AnkiConnect is installed")
            return False

        self._checkForDefaultDeck()
        self._buildNewDecksAsRequired(deck.getDeckNames())
        # Build new questions
        notes = self.buildAnkiNotes(deck.getQuestions())

        # TODO Get all question from that deck and
        # use this to verify questions need to be uploaded
        # self._removeAlreadyExistingQuestions()

        # Insert new question through the api
        self.connector.uploadNotes(notes)

    def _buildNewDecksAsRequired(self, deckNames: [str]):
        # Check decks exist for notes
        newDeckPaths = []
        for i in deckNames:
            fullDeckPath = self._getFullDeckPath(i)
            if fullDeckPath not in self.currentDecks and fullDeckPath not in newDeckPaths:
                newDeckPaths.append(fullDeckPath)

        # Create decks
        for deck in newDeckPaths:
            self.connector.createDeck(deck)

    def _getFullDeckPath(self, deckName: str):
        return self.defaultDeck + "::" + deckName

    def _checkForDefaultDeck(self):
        self.currentDecks = self.connector.getDeckNames()
        if self.defaultDeck not in self.currentDecks:
            self.connector.createDeck(self.defaultDeck)

    def buildAnkiNotes(self, ankiQuestions: [AnkiQuestion]):

        notes = []
        for i in ankiQuestions:
            notes.append(self._buildNote(i))

        finalNotes = {}
        finalNotes["notes"] = notes
        return finalNotes

    def _buildNote(self, ankiQuestion: AnkiQuestion):

        # All decks stored under default deck
        if ankiQuestion.deckName == "" or ankiQuestion.deckName is None:
            # TODO log note was built on default deck
            deckName = self.defaultDeck
        else:
            deckName = self._getFullDeckPath(ankiQuestion.deckName)

        if ankiQuestion.getParameter("type") is not None:
            modelName = ankiQuestion.getParameter("type")
        else:
            modelName = "Basic"

        note = {"deckName": deckName, "modelName": modelName}
        note["tags"] = ankiQuestion.getTags()

        # Generate fields
        fields = {}
        fields["Front"] = ankiQuestion.question
        fields["Back"] = self._createAnswerString(ankiQuestion.getAnswers())

        note["fields"] = fields
        return note

    def _createAnswerString(self, answers: [str], bulletPoints: bool=True):
        result = ""
        if not bulletPoints:
            for i in answers:
                result += i + "<br>"  # HTML link break
        else:
            # Can only can create single level of indentation. Align
            # bulletpoints.
            result += "<ul style='list-style-position: inside;'>"
            for i in answers:
                if isinstance(i, str):
                    result += "<li>" + i + "</li>"
                elif isinstance(i, list):
                    result += self._createAnswerString(i)
                else:
                    raise Exception("Unsupported action with answer string")

            result += "</ul>"
        return result

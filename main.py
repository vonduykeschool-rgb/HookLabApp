"""
Hook Lab: a vault for OwenEighth song fragments.

Save lyric and melody ideas, tag each one with a mood, mark favorites,
filter the vault by mood, and shuffle 4 random fragments into a stanza.
The site never writes lyrics. Every line comes from what you typed in.
"""
import random
from dataclasses import dataclass
from drafter import *
from bakery import assert_equal

MOODS = ["Excited", "Serious", "Relaxed", "Happy", "Sad"]
KINDS = ["lyric", "melody"]
ALL = "All"
STANZA_LENGTH = 4


@dataclass
class Fragment:
    """
    One saved song idea.

    Attributes:
        text: The lyric or melody idea.
        mood: Excited, Serious, Relaxed, Happy, or Sad.
        kind: "lyric" or "melody".
        favorite: Whether it is marked as a favorite.
    """
    text: str
    mood: str
    kind: str
    favorite: bool


@dataclass
class State:
    """
    Everything the site remembers.

    Attributes:
        fragments: My vault. Saving adds one, deleting removes one.
        current_mood: Which mood the vault shows. Changed by [Filter].
        selected_index: Which fragment is open. Changed by [Open].
        last_stanza: The 4 lines from my latest shuffle. Changed by [Shuffle].
        message: Feedback like "Text can't be empty."
    """
    fragments: list[Fragment]
    current_mood: str
    selected_index: int
    last_stanza: list[str]
    message: str


# Helper functions

def format_fragment(fragment: Fragment) -> str:
    """Return a fragment as one line of text, with a * if it is a favorite."""
    label = fragment.text + " (" + fragment.mood + ", " + fragment.kind + ")"
    if fragment.favorite:
        return "* " + label
    return label


def filter_by_mood(fragments: list[Fragment], mood: str) -> list[Fragment]:
    """Return only the fragments whose mood matches (or all of them for "All")."""
    matches = []
    for fragment in fragments:
        if mood == ALL or fragment.mood == mood:
            matches.append(fragment)
    return matches


def count_favorites(fragments: list[Fragment]) -> int:
    """Count how many fragments are marked as favorites."""
    total = 0
    for fragment in fragments:
        if fragment.favorite:
            total = total + 1
    return total


# Routes

@route
def index(state: State) -> Page:
    """The home page: title, fragment count, and buttons to the other pages."""
    return Page(state, [
        Header("Hook Lab"),
        "You have " + str(len(state.fragments)) + " fragments ("
        + str(count_favorites(state.fragments)) + " favorites).",
        Button("Add", add_fragment),
        Button("Vault", vault),
        Button("Stanza", stanza),
    ])


@route
def add_fragment(state: State) -> Page:
    """The form for entering a new fragment."""
    return Page(state, [
        Header("Add a fragment"),
        state.message,
        "Text:", TextBox("new_text"),
        "Mood:", SelectBox("new_mood", MOODS),
        "Kind:", SelectBox("new_kind", KINDS),
        "Favorite?", CheckBox("is_favorite"),
        Button("Save", save_fragment),
        Button("Home", index),
    ])


@route
def save_fragment(state: State, new_text: str, new_mood: str,
                  new_kind: str, is_favorite: bool) -> Page:
    """Save the new fragment, or send the user back if the text is empty."""
    if new_text.strip() == "":
        state.message = "Text can't be empty."
        return add_fragment(state)
    state.fragments.append(Fragment(new_text.strip(), new_mood, new_kind, is_favorite))
    state.message = "Saved!"
    return vault(state)


@route
def vault(state: State) -> Page:
    """Show the fragments for the current mood, each with an Open button."""
    content = [
        Header("Vault"),
        state.message,
        "Mood:", SelectBox("mood_choice", [ALL] + MOODS, state.current_mood),
        Button("Filter", filter_vault),
    ]
    if len(filter_by_mood(state.fragments, state.current_mood)) == 0:
        content.append("No fragments yet.")
    for index_number, fragment in enumerate(state.fragments):
        if state.current_mood == ALL or fragment.mood == state.current_mood:
            content.append(format_fragment(fragment))
            content.append(Button("Open", view_fragment, [Argument("index", index_number)]))
    content.append(Button("Home", index))
    state.message = ""
    return Page(state, content)


@route
def filter_vault(state: State, mood_choice: str) -> Page:
    """Change which mood the vault shows."""
    state.current_mood = mood_choice
    return vault(state)


@route
def view_fragment(state: State, index: int) -> Page:
    """Show one fragment with Favorite and Delete buttons."""
    state.selected_index = index
    fragment = state.fragments[index]
    return Page(state, [
        Header("Fragment"),
        format_fragment(fragment),
        Button("Favorite", toggle_favorite),
        Button("Delete", delete_fragment),
        Button("Back to Vault", vault),
    ])


@route
def toggle_favorite(state: State) -> Page:
    """Flip the open fragment's favorite on or off."""
    fragment = state.fragments[state.selected_index]
    fragment.favorite = not fragment.favorite
    return view_fragment(state, state.selected_index)


@route
def delete_fragment(state: State) -> Page:
    """Remove the open fragment from the vault."""
    state.fragments.pop(state.selected_index)
    state.selected_index = 0
    state.message = "Deleted."
    return vault(state)


@route
def stanza(state: State) -> Page:
    """Pick a mood and show the last shuffled stanza."""
    content = [
        Header("Stanza"),
        "Mood:", SelectBox("stanza_mood", MOODS),
        Button("Shuffle", shuffle_stanza),
    ]
    for line in state.last_stanza:
        content.append(line)
    content.append(state.message)
    content.append(Button("Home", index))
    state.message = ""
    return Page(state, content)


@route
def shuffle_stanza(state: State, stanza_mood: str) -> Page:
    """Pick 4 random fragments of one mood, or explain why it can't."""
    matches = filter_by_mood(state.fragments, stanza_mood)
    if len(matches) < STANZA_LENGTH:
        state.last_stanza = []
        state.message = ("You need at least 4 " + stanza_mood
                         + " fragments. Add more!")
    else:
        picked = random.sample(matches, STANZA_LENGTH)
        state.last_stanza = []
        for fragment in picked:
            state.last_stanza.append(fragment.text)
    return stanza(state)


# Tests

late_night = Fragment("late night on the 95", "Sad", "lyric", True)
hum_low = Fragment("hum it low", "Sad", "melody", False)
we_dont_fold = Fragment("we don't fold", "Serious", "lyric", False)

assert_equal(format_fragment(late_night), "* late night on the 95 (Sad, lyric)")
assert_equal(format_fragment(hum_low), "hum it low (Sad, melody)")
assert_equal(filter_by_mood([late_night, hum_low, we_dont_fold], "Sad"), [late_night, hum_low])
assert_equal(filter_by_mood([late_night, we_dont_fold], ALL), [late_night, we_dont_fold])
assert_equal(filter_by_mood([], "Happy"), [])
assert_equal(count_favorites([late_night, hum_low, we_dont_fold]), 1)
assert_equal(count_favorites([]), 0)

assert_equal(
    index(State([], ALL, 0, [], "")),
    Page(State([], ALL, 0, [], ""), [
        Header("Hook Lab"),
        "You have 0 fragments (0 favorites).",
        Button("Add", add_fragment),
        Button("Vault", vault),
        Button("Stanza", stanza),
    ]))

assert_equal(
    save_fragment(State([], ALL, 0, [], ""), "   ", "Sad", "lyric", False),
    Page(State([], ALL, 0, [], "Text can't be empty."), [
        Header("Add a fragment"),
        "Text can't be empty.",
        "Text:", TextBox("new_text"),
        "Mood:", SelectBox("new_mood", MOODS),
        "Kind:", SelectBox("new_kind", KINDS),
        "Favorite?", CheckBox("is_favorite"),
        Button("Save", save_fragment),
        Button("Home", index),
    ]))

assert_equal(
    shuffle_stanza(State([], ALL, 0, [], ""), "Happy"),
    Page(State([], ALL, 0, [], ""), [
        Header("Stanza"),
        "Mood:", SelectBox("stanza_mood", MOODS),
        Button("Shuffle", shuffle_stanza),
        "You need at least 4 Happy fragments. Add more!",
        Button("Home", index),
    ]))


# Site setup

set_site_information(
    author="Justinvd@udel.edu",
    description="""Hook Lab is a vault for song fragments. Save lyric and
    melody ideas tagged by mood, filter them, mark favorites, and shuffle
    them into random 4-line stanzas.""",
    sources=["Official Drafter documentation"],
    planning=["plan.pdf"],
    links=["https://github.com/vonduykeschool-rgb/Hook-Lab"]
)
hide_debug_information()
set_website_title("Hook Lab")
set_website_framed(False)

start_server(State([], ALL, 0, [], ""))

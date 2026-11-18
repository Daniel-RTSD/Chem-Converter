"""Chemistry Helper website built with Drafter.

This program takes a series of inputs from the user through a website and
puts out a series of results based on those inputs, relying on chemistry and
a chemical element library to compute the end results. Tools included are an
element library, a stoichiometry (equation balancing) calculator, moles/grams
converters, an enthalpy calculator backed by a library of standard
enthalpies (ΔH), an instructions page, and a page of previous results.

Advanced techniques used (not covered in class):
    * ``Callable`` from the ``typing`` module is used only as a type hint, so
      a function can be passed in as a parameter (see ``converter_page``).
    * Drafter's ``assert_equal`` is used to compare whole ``Page`` objects in
      the route tests at the bottom of this file.
    * ``lambda`` (a tiny unnamed function) and ``try``/``except`` with
      ``NameError`` are used in ``style_website`` so that a styling helper
      missing from an older Drafter version cannot crash the website.
"""
from drafter import *
from dataclasses import dataclass
from typing import Callable, Optional
from math import ceil


@dataclass
class element:
    """A single chemical element in the element library.

    Attributes:
        Chemical_symbol: The one or two letter symbol, e.g. "Na".
        Molar_mass: The molar mass of the element in grams per mole.
        Atomic_number: The number of protons in the element.
    """
    Chemical_symbol: str
    Molar_mass: float
    Atomic_number: int


@dataclass
class Compound:
    """A compound in the enthalpy (delta H) library.

    Attributes:
        formula: The chemical formula, e.g. "H2O".
        name: A readable name including its state, e.g. "Water (liquid)".
        enthalpy: Standard enthalpy of formation in kJ per mole at 25 °C.
    """
    formula: str
    name: str
    enthalpy: float


@dataclass
class Result:
    """One saved calculation shown on the Previous Results page.

    Attributes:
        tool: Name of the tool that produced the result.
        result: The text of the result.
    """
    tool: str
    result: str


@dataclass
class State:
    """Data that persists across every page of the website.

    Attributes:
        library: The element library (a list of element instances).
        history: Every successful calculation made so far (a list of
            Result instances). A new Result is added after each calculation.
        result: Result or error message shown on the current calculator.
            Set by every calculate route and cleared when returning home.
        calculation_count: How many successful calculations have been made.
        last_tool: Name of the tool that made the latest calculation.
        library_section: The atomic number range chosen in the select box on
            the element library page (changed by show_library_section).
        round_up: Whether the check box on the home page asked for results
            to be rounded up to the nearest integer (changed by
            set_rounding).
        compounds: The enthalpy library (a list of Compound instances) used
            by the enthalpy calculator and the ΔH library page.
    """
    library: list[element]
    history: list[Result]
    result: str
    calculation_count: int
    last_tool: str
    library_section: str
    round_up: bool
    compounds: list[Compound]


LIBRARY_SECTIONS = ["All elements", "1-20", "21-54", "55-86", "87-118"]
NO_COMPOUND = "(none)"
CUSTOM_COMPOUND = "Custom ΔH value"
METHANE = "CH4 - Methane (gas)"
OXYGEN = "O2 - Oxygen (gas)"
CARBON_DIOXIDE = "CO2 - Carbon dioxide (gas)"
WATER = "H2O - Water (liquid)"
ENTHALPY_HELP = [
    "Find ΔH total: the heat a reaction releases (negative) or absorbs "
    "(positive), in kJ.",
    "How to use it:",
    "1. Balance your reaction first (the Stoichiometry Calculator can do it).",
    "2. For each reactant and product, pick the compound from its list. "
    "Its ΔH is filled in for you.",
    "3. Type each coefficient: the number in front of the compound in the "
    "balanced equation (no number means 1).",
    "4. Press Calculate. ΔH total = (sum of products) − (sum of reactants), "
    "each ΔH multiplied by its coefficient.",
    "Leave a list on (none) if you have fewer than two reactants or "
    "products. If your compound is not listed, choose 'Custom ΔH value' "
    "and type its ΔH yourself.",
]
INSTRUCTION_LINES = [
    "Formulas are case-sensitive: write NaCl, not nacl. Use letters and "
    "digits only, e.g. H2O.",
    "Coefficient: the number in front of a formula in a balanced equation. "
    "In 2H2 + O2 -> 2H2O the coefficients are 2, 1 and 2. A missing number "
    "means 1.",
    "Stoichiometry: balancing an equation means finding the coefficients so "
    "both sides have the same atoms.",
    "Molar mass: the mass in grams of one mole of a substance (g/mol).",
    "ΔH (enthalpy change): heat released or absorbed in kJ. Negative means "
    "the reaction releases heat (exothermic); positive means it absorbs "
    "heat (endothermic).",
    "ΔH of formation: the heat change for making one mole of a compound "
    "from its elements. The ΔH Library lists many of them, so you do not "
    "have to look them up.",
    "Rounding: tick the box in Settings on the home page to round every "
    "result up to the nearest integer.",
]
FONT_LINK = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Nunito:wght@400;700;800&display=swap">'
)
BUTTON_CSS = (
    "display:block !important; width:100%; max-width:420px; "
    "margin:14px 0 4px !important; padding:12px 18px !important; "
    "border:none !important; border-radius:12px !important; "
    "background:linear-gradient(135deg,#14b8a6,#0f766e) !important; "
    "color:#ffffff !important; font-size:1em !important; "
    "font-weight:700 !important; cursor:pointer; text-align:center; "
    "box-shadow:0 3px 8px rgba(15,118,110,0.30); "
    "transition:transform 0.12s, box-shadow 0.12s;"
)
# Each rule is (CSS selector, CSS declarations), given to Drafter one by one.
THEME_RULES = [
    ("body",
     "font-family:'Nunito','Segoe UI',Arial,sans-serif; color:#134e4a; "
     "background:linear-gradient(135deg,#ecfdf5,#e0f2fe) fixed; "
     "margin:0; padding:24px 12px; line-height:1.6;"),
    ("form",
     "max-width:760px; margin:0 auto; background:#ffffff; "
     "padding:28px 34px; border-radius:18px; "
     "border-top:6px solid #14b8a6; "
     "box-shadow:0 10px 30px rgba(15,118,110,0.18);"),
    ("h1",
     "color:#0f766e; font-size:1.9em; font-weight:800; margin-top:0; "
     "padding-bottom:8px; border-bottom:2px solid #ccfbf1;"),
    ("h2", "color:#115e59; margin-top:28px;"),
    ("button, input[type=submit]", BUTTON_CSS),
    ("button:hover, input[type=submit]:hover",
     "transform:translateY(-2px); "
     "box-shadow:0 6px 14px rgba(15,118,110,0.40);"),
    ('input[value="Home"], input[value="Back"], '
     'button[value="Home"], button[value="Back"]',
     "background:#f0fdfa !important; color:#0f766e !important; "
     "border:2px solid #14b8a6 !important; box-shadow:none;"),
    ("input[type=text], select",
     "max-width:100%; padding:10px 12px; margin:4px 8px 8px 0; border:2px solid #99f6e4; "
     "border-radius:10px; font-family:inherit; font-size:1em; "
     "background:#f8fffd; color:#134e4a;"),
    ("input[type=text]:focus, select:focus",
     "outline:none; border-color:#14b8a6; "
     "box-shadow:0 0 0 3px rgba(20,184,166,0.25);"),
    ("input[type=checkbox]",
     "accent-color:#0f766e; width:20px; height:20px; vertical-align:middle;"),
    ("table",
     "width:100%; border-collapse:collapse; margin:16px 0; "
     "border-radius:12px; overflow:hidden; "
     "box-shadow:0 2px 10px rgba(15,118,110,0.15);"),
    ("th",
     "background:#0f766e; color:#ffffff; padding:10px 14px; text-align:left;"),
    ("td", "padding:9px 14px; border-bottom:1px solid #ccfbf1;"),
    ("tr:nth-child(even) td", "background:#f0fdfa;"),
    ("tr:hover td", "background:#ccfbf1;"),
]
ELEMENTS = [
    element("H", 1.008, 1),
    element("He", 4.0026, 2),
    element("Li", 6.94, 3),
    element("Be", 9.0122, 4),
    element("B", 10.81, 5),
    element("C", 12.011, 6),
    element("N", 14.007, 7),
    element("O", 15.999, 8),
    element("F", 18.998, 9),
    element("Ne", 20.180, 10),
    element("Na", 22.990, 11),
    element("Mg", 24.305, 12),
    element("Al", 26.982, 13),
    element("Si", 28.085, 14),
    element("P", 30.974, 15),
    element("S", 32.06, 16),
    element("Cl", 35.45, 17),
    element("Ar", 39.948, 18),
    element("K", 39.098, 19),
    element("Ca", 40.078, 20),
    element("Sc", 44.956, 21),
    element("Ti", 47.867, 22),
    element("V", 50.942, 23),
    element("Cr", 51.996, 24),
    element("Mn", 54.938, 25),
    element("Fe", 55.845, 26),
    element("Co", 58.933, 27),
    element("Ni", 58.693, 28),
    element("Cu", 63.546, 29),
    element("Zn", 65.38, 30),
    element("Ga", 69.723, 31),
    element("Ge", 72.630, 32),
    element("As", 74.922, 33),
    element("Se", 78.971, 34),
    element("Br", 79.904, 35),
    element("Kr", 83.798, 36),
    element("Rb", 85.468, 37),
    element("Sr", 87.62, 38),
    element("Y", 88.906, 39),
    element("Zr", 91.224, 40),
    element("Nb", 92.906, 41),
    element("Mo", 95.95, 42),
    element("Tc", 98.0, 43),
    element("Ru", 101.07, 44),
    element("Rh", 102.91, 45),
    element("Pd", 106.42, 46),
    element("Ag", 107.87, 47),
    element("Cd", 112.41, 48),
    element("In", 114.82, 49),
    element("Sn", 118.71, 50),
    element("Sb", 121.76, 51),
    element("Te", 127.60, 52),
    element("I", 126.90, 53),
    element("Xe", 131.29, 54),
    element("Cs", 132.91, 55),
    element("Ba", 137.33, 56),
    element("La", 138.91, 57),
    element("Ce", 140.12, 58),
    element("Pr", 140.91, 59),
    element("Nd", 144.24, 60),
    element("Pm", 145.0, 61),
    element("Sm", 150.36, 62),
    element("Eu", 151.96, 63),
    element("Gd", 157.25, 64),
    element("Tb", 158.93, 65),
    element("Dy", 162.50, 66),
    element("Ho", 164.93, 67),
    element("Er", 167.26, 68),
    element("Tm", 168.93, 69),
    element("Yb", 173.05, 70),
    element("Lu", 174.97, 71),
    element("Hf", 178.49, 72),
    element("Ta", 180.95, 73),
    element("W", 183.84, 74),
    element("Re", 186.21, 75),
    element("Os", 190.23, 76),
    element("Ir", 192.22, 77),
    element("Pt", 195.08, 78),
    element("Au", 196.97, 79),
    element("Hg", 200.59, 80),
    element("Tl", 204.38, 81),
    element("Pb", 207.2, 82),
    element("Bi", 208.98, 83),
    element("Po", 209.0, 84),
    element("At", 210.0, 85),
    element("Rn", 222.0, 86),
    element("Fr", 223.0, 87),
    element("Ra", 226.0, 88),
    element("Ac", 227.0, 89),
    element("Th", 232.04, 90),
    element("Pa", 231.04, 91),
    element("U", 238.03, 92),
    element("Np", 237.0, 93),
    element("Pu", 244.0, 94),
    element("Am", 243.0, 95),
    element("Cm", 247.0, 96),
    element("Bk", 247.0, 97),
    element("Cf", 251.0, 98),
    element("Es", 252.0, 99),
    element("Fm", 257.0, 100),
    element("Md", 258.0, 101),
    element("No", 259.0, 102),
    element("Lr", 266.0, 103),
    element("Rf", 267.0, 104),
    element("Db", 268.0, 105),
    element("Sg", 269.0, 106),
    element("Bh", 270.0, 107),
    element("Hs", 277.0, 108),
    element("Mt", 278.0, 109),
    element("Ds", 281.0, 110),
    element("Rg", 282.0, 111),
    element("Cn", 285.0, 112),
    element("Nh", 286.0, 113),
    element("Fl", 289.0, 114),
    element("Mc", 290.0, 115),
    element("Lv", 293.0, 116),
    element("Ts", 294.0, 117),
    element("Og", 294.0, 118)
]
COMPOUNDS = [
    Compound("H2", "Hydrogen (gas)", 0.0),
    Compound("O2", "Oxygen (gas)", 0.0),
    Compound("N2", "Nitrogen (gas)", 0.0),
    Compound("Cl2", "Chlorine (gas)", 0.0),
    Compound("C", "Carbon, graphite (solid)", 0.0),
    Compound("Fe", "Iron (solid)", 0.0),
    Compound("Al", "Aluminum (solid)", 0.0),
    Compound("Mg", "Magnesium (solid)", 0.0),
    Compound("Na", "Sodium (solid)", 0.0),
    Compound("Ca", "Calcium (solid)", 0.0),
    Compound("H2O", "Water (liquid)", -285.8),
    Compound("H2O(g)", "Water vapor (gas)", -241.8),
    Compound("H2O2", "Hydrogen peroxide (liquid)", -187.8),
    Compound("CO", "Carbon monoxide (gas)", -110.5),
    Compound("CO2", "Carbon dioxide (gas)", -393.5),
    Compound("CH4", "Methane (gas)", -74.8),
    Compound("C2H6", "Ethane (gas)", -84.7),
    Compound("C3H8", "Propane (gas)", -103.8),
    Compound("C4H10", "Butane (gas)", -125.7),
    Compound("C2H4", "Ethylene (gas)", 52.4),
    Compound("C2H2", "Acetylene (gas)", 227.4),
    Compound("C6H6", "Benzene (liquid)", 49.1),
    Compound("CH3OH", "Methanol (liquid)", -238.7),
    Compound("C2H5OH", "Ethanol (liquid)", -277.7),
    Compound("C6H12O6", "Glucose (solid)", -1273.3),
    Compound("NH3", "Ammonia (gas)", -45.9),
    Compound("NO", "Nitrogen monoxide (gas)", 90.3),
    Compound("NO2", "Nitrogen dioxide (gas)", 33.2),
    Compound("N2O", "Nitrous oxide (gas)", 82.1),
    Compound("SO2", "Sulfur dioxide (gas)", -296.8),
    Compound("SO3", "Sulfur trioxide (gas)", -395.7),
    Compound("H2S", "Hydrogen sulfide (gas)", -20.6),
    Compound("HCl", "Hydrogen chloride (gas)", -92.3),
    Compound("NaCl", "Sodium chloride (solid)", -411.2),
    Compound("CaO", "Calcium oxide (solid)", -635.1),
    Compound("CaCO3", "Calcium carbonate (solid)", -1206.9),
    Compound("Ca(OH)2", "Calcium hydroxide (solid)", -986.1),
    Compound("MgO", "Magnesium oxide (solid)", -601.6),
    Compound("Fe2O3", "Iron(III) oxide (solid)", -824.2),
    Compound("Al2O3", "Aluminum oxide (solid)", -1675.7),
    Compound("O3", "Ozone (gas)", 142.7),
]


def format_number(value: float, round_up: bool) -> str:
    """Turns a calculated number into text, optionally rounding it up.

    The value is first rounded to 4 decimal places (to remove tiny floating
    point errors such as 2.0000000000000004) and then, if round_up is True,
    rounded up to the next integer.

    Args:
        value: The number to display.
        round_up: True to round up to the nearest integer (ceiling).

    Returns:
        The number as text, e.g. "111.69", or "112" when round_up is True.
    """
    value = round(value, 4)
    if round_up:
        return str(ceil(value))
    return str(value)


def moles_to_mass_converter(symbol: str, mole_number: str,
                            library: list[element],
                            round_up: bool = False) -> str:
    """Converts moles of an element into grams.

    Args:
        symbol: The element symbol, e.g. "Fe".
        mole_number: The number of moles, as typed by the user.
        library: The element library to search for the symbol.
        round_up: True to round the answer up to the nearest integer.

    Returns:
        The mass in grams (as text), or an error message if the input
        is invalid.
    """
    symbol = symbol.strip()
    mole_number = mole_number.strip()
    if not mole_number:
        return "Enter a valid number of moles."
    try:
        mole_number = float(mole_number)
    except ValueError:
        return "Moles must be a number."
    if mole_number < 0:
        return "Moles can't be negative."
    for chemical in library:
        if chemical.Chemical_symbol == symbol:
            grams = mole_number * chemical.Molar_mass
            return format_number(grams, round_up) + " grams"
    return "Not a valid element."


def mass_to_moles_converter(symbol: str, grams_number: str,
                            library: list[element],
                            round_up: bool = False) -> str:
    """Converts grams of an element into moles.

    Args:
        symbol: The element symbol, e.g. "Fe".
        grams_number: The number of grams, as typed by the user.
        library: The element library to search for the symbol.
        round_up: True to round the answer up to the nearest integer.

    Returns:
        The amount in moles (as text), or an error message if the input
        is invalid.
    """
    symbol = symbol.strip()
    grams_number = grams_number.strip()
    if not grams_number:
        return "Enter a valid number of grams."
    try:
        grams_number = float(grams_number)
    except ValueError:
        return "Grams must be a number."
    if grams_number < 0:
        return "Grams can't be negative."
    for chemical in library:
        if chemical.Chemical_symbol == symbol:
            moles = grams_number / chemical.Molar_mass
            return format_number(moles, round_up) + " moles"
    return "Not a valid element."


def sum_enthalpy(enthalpies: list[float], coefficients: list[float]) -> float:
    """Adds up enthalpy times coefficient for each compound on one side.

    Args:
        enthalpies: The delta H of each compound.
        coefficients: The coefficient of each compound, in the same order.

    Returns:
        The sum of enthalpy * coefficient over all compounds.
    """
    total = 0.0
    for position in range(len(enthalpies)):
        total += enthalpies[position] * coefficients[position]
    return total


def enthalpy_calculator(enthalpy_reactant_1: str, reactant_moles_1: str,
                        enthalpy_reactant_2: str, reactant_moles_2: str,
                        enthalpy_product_1: str, product_moles_1: str,
                        enthalpy_product_2: str, product_moles_2: str,
                        round_up: bool = False) -> str:
    """Calculates the total change in enthalpy of a reaction.

    Uses delta H total = sum(products) - sum(reactants), where each term is
    the enthalpy multiplied by the coefficient.

    Args:
        enthalpy_reactant_1: Delta H of the first reactant.
        reactant_moles_1: Coefficient of the first reactant.
        enthalpy_reactant_2: Delta H of the second reactant.
        reactant_moles_2: Coefficient of the second reactant.
        enthalpy_product_1: Delta H of the first product.
        product_moles_1: Coefficient of the first product.
        enthalpy_product_2: Delta H of the second product.
        product_moles_2: Coefficient of the second product.
        round_up: True to round the answer up to the nearest integer.

    Returns:
        The total delta H (as text), or an error message if any input is
        not a number or a coefficient is negative.
    """
    try:
        enthalpy_reactant_1 = float(enthalpy_reactant_1)
        enthalpy_reactant_2 = float(enthalpy_reactant_2)
        enthalpy_product_1 = float(enthalpy_product_1)
        enthalpy_product_2 = float(enthalpy_product_2)
    except ValueError:
        return "Reactants and product enthalpies need to be a number"
    try:
        reactant_moles_1 = float(reactant_moles_1)
        reactant_moles_2 = float(reactant_moles_2)
        product_moles_1 = float(product_moles_1)
        product_moles_2 = float(product_moles_2)
    except ValueError:
        return "Reactants and product coefficients need to be a number"
    if min(reactant_moles_1, reactant_moles_2,
           product_moles_1, product_moles_2) < 0:
        return "Coefficients can't be negative"
    products_total = sum_enthalpy([enthalpy_product_1, enthalpy_product_2],
                                  [product_moles_1, product_moles_2])
    reactants_total = sum_enthalpy([enthalpy_reactant_1, enthalpy_reactant_2],
                                   [reactant_moles_1, reactant_moles_2])
    total = format_number(products_total - reactants_total, round_up)
    return "ΔH total = " + total + " kJ"


def compound_label(compound: Compound) -> str:
    """Makes the text shown for a compound in a select box.

    Args:
        compound: The compound to describe.

    Returns:
        Text such as "H2O - Water (liquid)".
    """
    return compound.formula + " - " + compound.name


def compound_options(compounds: list[Compound]) -> list[str]:
    """Lists every choice for a compound select box.

    Args:
        compounds: The enthalpy library.

    Returns:
        "(none)", "Custom ΔH value", then one label per compound.
    """
    options = [NO_COMPOUND, CUSTOM_COMPOUND]
    for compound in compounds:
        options.append(compound_label(compound))
    return options


def find_compound(choice: str, compounds: list[Compound]) -> Optional[Compound]:
    """Finds the compound that matches a select box choice.

    Args:
        choice: A label made by compound_label.
        compounds: The enthalpy library to search.

    Returns:
        The matching Compound, or None if there is no match.
    """
    formula = choice.split(" - ")[0]
    for compound in compounds:
        if compound.formula == formula:
            return compound
    return None


def read_slot(choice: str, coefficient: str, custom: str,
              compounds: list[Compound]) -> list[str]:
    """Turns one reactant or product slot into text for enthalpy_calculator.

    Args:
        choice: The select box choice for this slot.
        coefficient: The coefficient typed by the user.
        custom: The custom delta H typed by the user.
        compounds: The enthalpy library.

    Returns:
        A list [delta H text, coefficient text]. An unused slot gives
        ["0", "0"]. Text that is not a number is passed on unchanged so
        enthalpy_calculator can report it.
    """
    if choice == NO_COMPOUND:
        return ["0", "0"]
    if choice == CUSTOM_COMPOUND:
        return [custom.strip(), coefficient.strip()]
    compound = find_compound(choice, compounds)
    if compound is None:
        return ["", coefficient.strip()]
    return [str(compound.enthalpy), coefficient.strip()]


def parse_formula(formula: str) -> dict:
    """Counts the atoms of each element in a chemical formula.

    Parentheses are not supported. Characters that are not letters or
    digits are skipped.

    Args:
        formula: A chemical formula such as "H2O".

    Returns:
        A dictionary mapping element symbols to atom counts, e.g.
        {"H": 2, "O": 1}.
    """
    elements = {}
    i = 0

    while i < len(formula):
        if formula[i].isupper():
            symbol = formula[i]
            i += 1

            if i < len(formula) and formula[i].islower():
                symbol += formula[i]
                i += 1

            number = ""

            while i < len(formula) and formula[i].isdigit():
                number += formula[i]
                i += 1

            if number == "":
                number = 1
            else:
                number = int(number)

            if symbol in elements:
                elements[symbol] += number
            else:
                elements[symbol] = number
        else:
            i += 1

    return elements


def is_valid_formula(formula: str, library: list[element]) -> bool:
    """Checks that a formula only uses known elements and plain characters.

    Args:
        formula: A chemical formula such as "H2O".
        library: The element library holding every valid symbol.

    Returns:
        True if the formula is non-empty, contains only letters and digits,
        and every element in it is in the library. False otherwise.
    """
    if not formula or not formula.isalnum():
        return False
    counts = parse_formula(formula)
    for symbol in counts:
        found = False
        for chemical in library:
            if chemical.Chemical_symbol == symbol:
                found = True
        if not found:
            return False
    return bool(counts)


def collect_elements(compounds: list[dict]) -> list[str]:
    """Lists every element that appears in any of the compounds.

    Args:
        compounds: Dictionaries of atom counts, as made by parse_formula.

    Returns:
        Each element symbol once, in the order first seen.
    """
    all_elements = []
    for compound in compounds:
        for symbol in compound:
            if symbol not in all_elements:
                all_elements.append(symbol)
    return all_elements


def is_balanced(coefficients: list[int], compounds: list[dict],
                all_elements: list[str]) -> bool:
    """Checks whether coefficients give equal atom counts on both sides.

    Args:
        coefficients: Four coefficients: reactant 1, reactant 2, product 1,
            product 2.
        compounds: The four atom-count dictionaries in the same order.
        all_elements: Every element symbol that appears in the reaction.

    Returns:
        True if every element has the same count on both sides.
    """
    for symbol in all_elements:
        reactant_count = (
            coefficients[0] * compounds[0].get(symbol, 0)
            + coefficients[1] * compounds[1].get(symbol, 0)
        )
        product_count = (
            coefficients[2] * compounds[2].get(symbol, 0)
            + coefficients[3] * compounds[3].get(symbol, 0)
        )
        if reactant_count != product_count:
            return False
    return True


def format_equation(coefficients: list[int], formulas: list[str]) -> str:
    """Writes a reaction as text with its coefficients.

    Args:
        coefficients: Four coefficients: reactant 1, reactant 2, product 1,
            product 2.
        formulas: The four formulas in the same order.

    Returns:
        Text such as "2H2 + 1O2 -> 1H2O + 1H2O".
    """
    return (
        str(coefficients[0]) + formulas[0] + " + "
        + str(coefficients[1]) + formulas[1] + " -> "
        + str(coefficients[2]) + formulas[2] + " + "
        + str(coefficients[3]) + formulas[3]
    )


def balance_reaction(r1: str, r2: str, p1: str, p2: str) -> str:
    """Balances a reaction of two reactants and two products.

    Tries every combination of coefficients from 1 to 20 and returns the
    first one that gives each element the same count on both sides.

    Args:
        r1: The first reactant formula.
        r2: The second reactant formula.
        p1: The first product formula.
        p2: The second product formula.

    Returns:
        The balanced equation as text, or "No balance found." if no
        coefficients from 1 to 20 work.
    """
    compounds = [parse_formula(r1), parse_formula(r2),
                 parse_formula(p1), parse_formula(p2)]
    all_elements = collect_elements(compounds)

    for a in range(1, 21):
        for b in range(1, 21):
            for c in range(1, 21):
                for d in range(1, 21):
                    if is_balanced([a, b, c, d], compounds, all_elements):
                        return format_equation([a, b, c, d], [r1, r2, p1, p2])

    return "No balance found."


def save_result(state: State, tool: str) -> None:
    """Adds the current result to the history and updates the counters.

    Args:
        state: The website state; its history, calculation_count and
            last_tool are changed.
        tool: Name of the tool that produced the result.
    """
    state.history.append(Result(tool, state.result))
    state.calculation_count += 1
    state.last_tool = tool


@route
def index(state: State) -> Page:
    """Home page with a button and description for every tool.

    Also clears any old result so each tool starts fresh, and holds the
    rounding check box that applies to every calculation.

    Args:
        state: The website state.

    Returns:
        The home page.
    """
    state.result = ""
    return Page(state, [
        Header("⚗️ Welcome to the Chemistry Helper website!"),
        Button("📖 Element Library", element_library),
        "Browse every element with its molar mass and atomic number.",
        Button("🧪 Stoichiometry Calculator", stoichiometry),
        "Balance a chemical equation.",
        Button("🔥 Enthalpy Calculator", enthalpy),
        "Find the total change in enthalpy (ΔH) of a reaction. "
        "Pick compounds from a list; no need to look up ΔH values.",
        Button("📚 ΔH Library", enthalpy_library),
        "Browse standard enthalpies of formation for common compounds.",
        Button("⚖️ Moles/Grams Converter", converter),
        "Convert between moles and grams for an element.",
        Button("📋 Previous Results", results),
        "See everything you have calculated this session.",
        Button("❓ Instructions", instructions),
        "New here? Learn what coefficients, ΔH and the other terms mean.",
        Header("⚙️ Settings"),
        "Round every calculation result up to the nearest integer:",
        CheckBox("round_up", state.round_up),
        Button("Save Settings", set_rounding),
    ])


@route
def set_rounding(state: State, round_up: bool) -> Page:
    """Saves whether calculation results should be rounded up.

    Args:
        state: The website state; its round_up field is changed.
        round_up: The value of the check box on the home page.

    Returns:
        The home page.
    """
    state.round_up = round_up
    return index(state)


def filter_library(library: list[element], section: str) -> list[element]:
    """Picks the elements that fall in the chosen atomic number range.

    Args:
        library: The element library to filter.
        section: "All elements" or a range such as "21-54".

    Returns:
        The elements whose atomic number is inside the range. If the section
        is not a valid range, the whole library is returned.
    """
    if "-" not in section:
        return library
    bounds = section.split("-")
    low = int(bounds[0])
    high = int(bounds[1])
    chosen = []
    for chemical in library:
        if low <= chemical.Atomic_number <= high:
            chosen.append(chemical)
    return chosen


@route
def element_library(state: State) -> Page:
    """Table of the elements in the range chosen with the select box.

    Args:
        state: The website state; its library_section decides which
            elements are listed.

    Returns:
        The element library page.
    """
    rows = [["Elements", "Molar mass", "Atomic #"]]
    for chemical in filter_library(state.library, state.library_section):
        rows.append([chemical.Chemical_symbol, str(chemical.Molar_mass),
                     str(chemical.Atomic_number)])
    return Page(state, [
        Button("Home", index),
        Header("📖 Element Library"),
        "Atomic number range to show:",
        SelectBox("section", LIBRARY_SECTIONS, state.library_section),
        Button("Show", show_library_section),
        Table(rows),
    ])


@route
def show_library_section(state: State, section: str) -> Page:
    """Saves the range chosen in the select box and shows the library.

    Args:
        state: The website state; its library_section field is changed.
        section: The option picked in the select box.

    Returns:
        The element library page.
    """
    state.library_section = section
    return element_library(state)


@route
def stoichiometry(state: State) -> Page:
    """Stoichiometry calculator page; shows the latest result if any.

    Args:
        state: The website state; its result is displayed on the page.

    Returns:
        The stoichiometry calculator page.
    """
    return Page(state, [
        Header("🧪 Stoichiometry Calculator"),
        "Enter the formulas of your reaction (letters and digits only, "
        "e.g. H2 + O2 -> H2O + H2O2).",
        "Reactants:",
        TextBox("reactant1", ""),
        "+",
        TextBox("reactant2", ""),
        "Products:",
        TextBox("product1", ""),
        "+",
        TextBox("product2", ""),
        Button("Calculate", calculate_stoichiometry),
        state.result,
        Button("Home", index),
    ])


@route
def calculate_stoichiometry(state: State, reactant1: str, reactant2: str,
                            product1: str, product2: str) -> Page:
    """Balances the entered reaction and shows the answer.

    Args:
        state: The website state.
        reactant1: First reactant formula from the text box.
        reactant2: Second reactant formula from the text box.
        product1: First product formula from the text box.
        product2: Second product formula from the text box.

    Returns:
        The stoichiometry calculator page showing the result or an error.
    """
    compounds = [reactant1.strip(), reactant2.strip(),
                 product1.strip(), product2.strip()]
    for compound in compounds:
        if not is_valid_formula(compound, state.library):
            state.result = ("Invalid formula: '" + compound + "'. Use known "
                            "elements, letters and digits only.")
            return stoichiometry(state)
    state.result = balance_reaction(compounds[0], compounds[1],
                                    compounds[2], compounds[3])
    if "->" in state.result:
        save_result(state, "Stoichiometry")
    return stoichiometry(state)


@route
def converter(state: State) -> Page:
    """Menu for choosing a moles or grams conversion.

    Args:
        state: The website state.

    Returns:
        The converter menu page.
    """
    state.result = ""
    return Page(state, [
        Header("⚖️ Moles/Grams Converter"),
        "Choose a conversion:",
        Button("Moles to Grams", moles_to_grams),
        Button("Grams to Moles", grams_to_moles),
        Button("Home", index),
    ])


def converter_page(state: State, title: str, label: str,
                   action: Callable) -> Page:
    """Builds a converter page (not a route itself).

    Args:
        state: The website state; its result is displayed on the page.
        title: Heading of the page.
        label: Text describing the amount box, e.g. "Number of moles:".
        action: The route that runs when Convert is pressed.

    Returns:
        The converter page.
    """
    return Page(state, [
        Header(title),
        "Element symbol (e.g. Fe):",
        TextBox("symbol", ""),
        label,
        TextBox("amount", ""),
        Button("Convert", action),
        state.result,
        Button("Back", converter),
        Button("Home", index),
    ])


@route
def moles_to_grams(state: State) -> Page:
    """Moles-to-grams converter page.

    Args:
        state: The website state; its result is displayed on the page.

    Returns:
        The moles-to-grams page.
    """
    return converter_page(state, "⚖️ Moles to Grams", "Number of moles:",
                          calculate_moles_to_grams)


@route
def calculate_moles_to_grams(state: State, symbol: str, amount: str) -> Page:
    """Runs the moles-to-grams conversion.

    Args:
        state: The website state.
        symbol: Element symbol from the text box.
        amount: Number of moles from the text box.

    Returns:
        The moles-to-grams page showing the result or an error.
    """
    state.result = moles_to_mass_converter(symbol, amount, state.library,
                                         state.round_up)
    if state.result.endswith(" grams"):
        save_result(state, "Moles to Grams (" + symbol.strip() + ")")
    return moles_to_grams(state)


@route
def grams_to_moles(state: State) -> Page:
    """Grams-to-moles converter page.

    Args:
        state: The website state; its result is displayed on the page.

    Returns:
        The grams-to-moles page.
    """
    return converter_page(state, "⚖️ Grams to Moles", "Number of grams:",
                          calculate_grams_to_moles)


@route
def calculate_grams_to_moles(state: State, symbol: str, amount: str) -> Page:
    """Runs the grams-to-moles conversion.

    Args:
        state: The website state.
        symbol: Element symbol from the text box.
        amount: Number of grams from the text box.

    Returns:
        The grams-to-moles page showing the result or an error.
    """
    state.result = mass_to_moles_converter(symbol, amount, state.library,
                                         state.round_up)
    if state.result.endswith(" moles"):
        save_result(state, "Grams to Moles (" + symbol.strip() + ")")
    return grams_to_moles(state)


def slot_inputs(label: str, name: str, options: list[str]) -> list:
    """Builds the labeled inputs for one reactant or product (not a route).

    Args:
        label: Heading for the slot, e.g. "Reactant 1:".
        name: Prefix for the input names; the coefficient box is
            name + "_coefficient" and the custom box name + "_custom".
        options: The choices for the compound select box.

    Returns:
        A list of page components: label, select box, and two text boxes.
    """
    return [
        label,
        SelectBox(name, options, NO_COMPOUND),
        "Coefficient (the number in front of it in the balanced equation):",
        TextBox(name + "_coefficient", ""),
        "Custom ΔH in kJ/mol (only if you chose 'Custom ΔH value'):",
        TextBox(name + "_custom", ""),
    ]


@route
def enthalpy(state: State) -> Page:
    """Enthalpy calculator page; shows the latest result if any.

    Args:
        state: The website state; its result is displayed on the page.

    Returns:
        The enthalpy calculator page.
    """
    options = compound_options(state.compounds)
    return Page(state, [
        Header("🔥 Enthalpy Calculator")] + ENTHALPY_HELP + [
        Button("📚 Browse the ΔH Library", enthalpy_library),
    ] + slot_inputs("Reactant 1:", "reactant_1", options)
      + slot_inputs("Reactant 2:", "reactant_2", options)
      + slot_inputs("Product 1:", "product_1", options)
      + slot_inputs("Product 2:", "product_2", options) + [
        Button("Calculate", calculate_enthalpy),
        state.result,
        Button("Home", index),
    ])


@route
def calculate_enthalpy(state: State, reactant_1: str,
                       reactant_1_coefficient: str, reactant_1_custom: str,
                       reactant_2: str, reactant_2_coefficient: str,
                       reactant_2_custom: str, product_1: str,
                       product_1_coefficient: str, product_1_custom: str,
                       product_2: str, product_2_coefficient: str,
                       product_2_custom: str) -> Page:
    """Runs the enthalpy calculation using the ΔH library.

    Args:
        state: The website state.
        reactant_1: Select box choice for the first reactant.
        reactant_1_coefficient: Coefficient of the first reactant.
        reactant_1_custom: Custom delta H of the first reactant.
        reactant_2: Select box choice for the second reactant.
        reactant_2_coefficient: Coefficient of the second reactant.
        reactant_2_custom: Custom delta H of the second reactant.
        product_1: Select box choice for the first product.
        product_1_coefficient: Coefficient of the first product.
        product_1_custom: Custom delta H of the first product.
        product_2: Select box choice for the second product.
        product_2_coefficient: Coefficient of the second product.
        product_2_custom: Custom delta H of the second product.

    Returns:
        The enthalpy calculator page showing the result or an error.
    """
    if reactant_1 == NO_COMPOUND and reactant_2 == NO_COMPOUND:
        state.result = "Choose at least one reactant and one product."
    elif product_1 == NO_COMPOUND and product_2 == NO_COMPOUND:
        state.result = "Choose at least one reactant and one product."
    else:
        first_reactant = read_slot(reactant_1, reactant_1_coefficient,
                                   reactant_1_custom, state.compounds)
        second_reactant = read_slot(reactant_2, reactant_2_coefficient,
                                    reactant_2_custom, state.compounds)
        first_product = read_slot(product_1, product_1_coefficient,
                                  product_1_custom, state.compounds)
        second_product = read_slot(product_2, product_2_coefficient,
                                   product_2_custom, state.compounds)
        state.result = enthalpy_calculator(
            first_reactant[0], first_reactant[1],
            second_reactant[0], second_reactant[1],
            first_product[0], first_product[1],
            second_product[0], second_product[1],
            state.round_up,
        )
    if state.result.startswith("ΔH total"):
        save_result(state, "Enthalpy")
    return enthalpy(state)


@route
def enthalpy_library(state: State) -> Page:
    """Table of the standard enthalpy of formation of common compounds.

    Args:
        state: The website state.

    Returns:
        The ΔH library page.
    """
    rows = [["Formula", "Name", "ΔH of formation (kJ/mol)"]]
    for compound in state.compounds:
        rows.append([compound.formula, compound.name, str(compound.enthalpy)])
    return Page(state, [
        Button("Home", index),
        Header("📚 ΔH Library"),
        "Standard enthalpies of formation at 25 °C, in kJ/mol. Elements in "
        "their standard state (like O2 and H2) are 0. Values are rounded and "
        "can differ slightly between textbooks.",
        Button("🔥 Go to the Enthalpy Calculator", enthalpy),
        Table(rows),
    ])


@route
def instructions(state: State) -> Page:
    """Explains the terms and tools used on the website.

    Args:
        state: The website state.

    Returns:
        The instructions page.
    """
    return Page(state, [Header("❓ Instructions")] + INSTRUCTION_LINES + [
        Button("Home", index),
    ])


@route
def results(state: State) -> Page:
    """Table of every successful calculation made so far.

    Args:
        state: The website state.

    Returns:
        The previous results page.
    """
    content = [
        Header("📋 Previous Results"),
        "Total calculations: " + str(state.calculation_count),
        "Last tool used: " + state.last_tool,
    ]
    if len(state.history) == 0:
        content.append("Nothing calculated yet.")
    else:
        rows = [["Tool used", "Result"]]
        for entry in state.history:
            rows.append([entry.tool, entry.result])
        content.append(Table(rows))
    content.append(Button("Home", index))
    return Page(state, content)


def try_setup(action: Callable) -> bool:
    """Runs one website-styling step, ignoring it if Drafter lacks it.

    Args:
        action: A function that takes no arguments and calls a Drafter
            styling helper.

    Returns:
        True if the step ran, False if the helper does not exist in this
        version of Drafter (NameError) or takes different arguments
        (TypeError).
    """
    try:
        action()
        return True
    except (NameError, TypeError):
        return False


def style_website() -> None:
    """Gives the website its title, font and colors.

    This function only changes how the site looks by calling Drafter's
    setup helpers, so it cannot be unit tested (it returns nothing and its
    effect is only visible in the browser). Its helper try_setup is tested.
    """
    try_setup(lambda: set_website_title("Chemistry Helper"))
    try_setup(lambda: set_website_framed(False))
    try_setup(lambda: add_website_header(FONT_LINK))
    for selector, css in THEME_RULES:
        try_setup(lambda: add_website_css(selector, css))


# ---------------------------------------------------------------------------
# Unit tests. They are inside functions so that no global variables are made.
# Page-building helpers (stoichiometry, enthalpy, ...) are routes, so they are
# tested by comparing whole Pages; calculate routes are tested through the
# state fields they change, since their Page just repeats the page above.
# ---------------------------------------------------------------------------
def make_state(result: str = "") -> State:
    """Makes a fresh State for a test.

    Args:
        result: The starting result text.

    Returns:
        A State with the full element library and no history.
    """
    return State(ELEMENTS, [], result, 0, "None yet", "All elements", False,
                 COMPOUNDS)


def test_converters() -> None:
    """Tests the moles and grams converter functions."""
    library = ELEMENTS
    assert_equal(moles_to_mass_converter("Fe", "2", library), "111.69 grams")
    assert_equal(moles_to_mass_converter(" O ", "0", library), "0.0 grams")
    assert_equal(moles_to_mass_converter("Fe", "", library),
                 "Enter a valid number of moles.")
    assert_equal(moles_to_mass_converter("Fe", "1.2.3", library),
                 "Moles must be a number.")
    assert_equal(moles_to_mass_converter("Fe", "-1", library),
                 "Moles can't be negative.")
    assert_equal(moles_to_mass_converter("Xx", "1", library),
                 "Not a valid element.")
    assert_equal(mass_to_moles_converter("Fe", "111.69", library), "2.0 moles")
    assert_equal(mass_to_moles_converter("Fe", "", library),
                 "Enter a valid number of grams.")
    assert_equal(mass_to_moles_converter("Fe", "abc", library),
                 "Grams must be a number.")
    assert_equal(mass_to_moles_converter("Fe", "-5", library),
                 "Grams can't be negative.")
    assert_equal(mass_to_moles_converter("Xx", "1", library),
                 "Not a valid element.")


def test_enthalpy() -> None:
    """Tests the enthalpy functions."""
    assert_equal(sum_enthalpy([2.0, 3.0], [1.0, 2.0]), 8.0)
    assert_equal(sum_enthalpy([], []), 0.0)
    assert_equal(enthalpy_calculator("-74.8", "1", "0", "2",
                                     "-393.5", "1", "-285.8", "2"),
                 "ΔH total = -890.3 kJ")
    assert_equal(enthalpy_calculator("a", "1", "0", "2", "1", "1", "1", "2"),
                 "Reactants and product enthalpies need to be a number")
    assert_equal(enthalpy_calculator("1", "x", "0", "2", "1", "1", "1", "2"),
                 "Reactants and product coefficients need to be a number")
    assert_equal(enthalpy_calculator("1", "-1", "0", "2", "1", "1", "1", "2"),
                 "Coefficients can't be negative")


def test_formulas() -> None:
    """Tests the formula parsing and balancing functions."""
    assert_equal(parse_formula("H2O"), {"H": 2, "O": 1})
    assert_equal(parse_formula("C6H12O6"), {"C": 6, "H": 12, "O": 6})
    assert_equal(parse_formula("NaCl"), {"Na": 1, "Cl": 1})
    assert_equal(parse_formula(""), {})
    assert_equal(is_valid_formula("H2O", ELEMENTS), True)
    assert_equal(is_valid_formula("Ca(OH)2", ELEMENTS), False)
    assert_equal(is_valid_formula("Xx", ELEMENTS), False)
    assert_equal(is_valid_formula("", ELEMENTS), False)
    assert_equal(collect_elements([{"H": 2}, {"O": 1, "H": 1}]), ["H", "O"])
    assert_equal(is_balanced([1, 1, 1, 0], [{"H": 2}, {"O": 2},
                                            {"H": 2, "O": 1}, {}],
                             ["H", "O"]), False)
    assert_equal(is_balanced([2, 1, 1, 1], [{"H": 2}, {"O": 2},
                                            {"H": 2, "O": 1}, {"H": 2, "O": 1}],
                             ["H", "O"]), True)
    assert_equal(format_equation([1, 2, 3, 4], ["A", "B", "C", "D"]),
                 "1A + 2B -> 3C + 4D")
    assert_equal(balance_reaction("CH4", "O2", "CO2", "H2O"),
                 "1CH4 + 2O2 -> 1CO2 + 2H2O")
    assert_equal(balance_reaction("H2", "O2", "H2O", "H2O2"),
                 "3H2 + 2O2 -> 2H2O + 1H2O2")
    assert_equal(balance_reaction("H2", "O2", "H2O", "NaCl"),
                 "No balance found.")


def test_save_result() -> None:
    """Tests that save_result updates the history and both counters."""
    state = make_state("5 grams")
    save_result(state, "Test Tool")
    assert_equal(state.history, [Result("Test Tool", "5 grams")])
    assert_equal(state.calculation_count, 1)
    assert_equal(state.last_tool, "Test Tool")


def test_display_routes() -> None:
    """Tests the routes that only show a page by comparing whole Pages."""
    state = make_state("old result")
    assert_equal(index(state), Page(state, [
        Header("⚗️ Welcome to the Chemistry Helper website!"),
        Button("📖 Element Library", element_library),
        "Browse every element with its molar mass and atomic number.",
        Button("🧪 Stoichiometry Calculator", stoichiometry),
        "Balance a chemical equation.",
        Button("🔥 Enthalpy Calculator", enthalpy),
        "Find the total change in enthalpy (ΔH) of a reaction. "
        "Pick compounds from a list; no need to look up ΔH values.",
        Button("📚 ΔH Library", enthalpy_library),
        "Browse standard enthalpies of formation for common compounds.",
        Button("⚖️ Moles/Grams Converter", converter),
        "Convert between moles and grams for an element.",
        Button("📋 Previous Results", results),
        "See everything you have calculated this session.",
        Button("❓ Instructions", instructions),
        "New here? Learn what coefficients, ΔH and the other terms mean.",
        Header("⚙️ Settings"),
        "Round every calculation result up to the nearest integer:",
        CheckBox("round_up", False),
        Button("Save Settings", set_rounding),
    ]))
    assert_equal(state.result, "")

    small = State([element("H", 1.008, 1), element("He", 4.0026, 2)],
                  [], "", 0, "None yet", "All elements", False, [])
    assert_equal(element_library(small), Page(small, [
        Button("Home", index),
        Header("📖 Element Library"),
        "Atomic number range to show:",
        SelectBox("section", LIBRARY_SECTIONS, "All elements"),
        Button("Show", show_library_section),
        Table([["Elements", "Molar mass", "Atomic #"],
               ["H", "1.008", "1"], ["He", "4.0026", "2"]]),
    ]))

    state = make_state("old result")
    assert_equal(converter(state), Page(state, [
        Header("⚖️ Moles/Grams Converter"),
        "Choose a conversion:",
        Button("Moles to Grams", moles_to_grams),
        Button("Grams to Moles", grams_to_moles),
        Button("Home", index),
    ]))
    assert_equal(state.result, "")


def test_page_routes() -> None:
    """Tests the calculator page routes by comparing whole Pages."""
    state = make_state("shown result")
    assert_equal(stoichiometry(state), Page(state, [
        Header("🧪 Stoichiometry Calculator"),
        "Enter the formulas of your reaction (letters and digits only, "
        "e.g. H2 + O2 -> H2O + H2O2).",
        "Reactants:",
        TextBox("reactant1", ""),
        "+",
        TextBox("reactant2", ""),
        "Products:",
        TextBox("product1", ""),
        "+",
        TextBox("product2", ""),
        Button("Calculate", calculate_stoichiometry),
        "shown result",
        Button("Home", index),
    ]))
    assert_equal(moles_to_grams(state), Page(state, [
        Header("⚖️ Moles to Grams"),
        "Element symbol (e.g. Fe):",
        TextBox("symbol", ""),
        "Number of moles:",
        TextBox("amount", ""),
        Button("Convert", calculate_moles_to_grams),
        "shown result",
        Button("Back", converter),
        Button("Home", index),
    ]))
    assert_equal(grams_to_moles(state), Page(state, [
        Header("⚖️ Grams to Moles"),
        "Element symbol (e.g. Fe):",
        TextBox("symbol", ""),
        "Number of grams:",
        TextBox("amount", ""),
        Button("Convert", calculate_grams_to_moles),
        "shown result",
        Button("Back", converter),
        Button("Home", index),
    ]))
    options = compound_options(state.compounds)
    assert_equal(enthalpy(state), Page(state, [
        Header("🔥 Enthalpy Calculator")] + ENTHALPY_HELP + [
        Button("📚 Browse the ΔH Library", enthalpy_library),
    ] + slot_inputs("Reactant 1:", "reactant_1", options)
      + slot_inputs("Reactant 2:", "reactant_2", options)
      + slot_inputs("Product 1:", "product_1", options)
      + slot_inputs("Product 2:", "product_2", options) + [
        Button("Calculate", calculate_enthalpy),
        "shown result",
        Button("Home", index),
    ]))


def test_calculate_routes() -> None:
    """Tests each calculate route through the state fields it changes."""
    state = make_state()
    calculate_stoichiometry(state, "CH4", "O2", "CO2", "H2O")
    assert_equal(state.result, "1CH4 + 2O2 -> 1CO2 + 2H2O")
    assert_equal(state.last_tool, "Stoichiometry")
    assert_equal(state.calculation_count, 1)
    calculate_stoichiometry(state, "xyz", "O2", "CO2", "H2O")
    assert_equal(state.result, "Invalid formula: 'xyz'. Use known elements, "
                               "letters and digits only.")
    assert_equal(state.calculation_count, 1)

    state = make_state()
    calculate_moles_to_grams(state, "Fe", "2")
    assert_equal(state.result, "111.69 grams")
    assert_equal(state.history, [Result("Moles to Grams (Fe)", "111.69 grams")])
    calculate_moles_to_grams(state, "Fe", "abc")
    assert_equal(state.result, "Moles must be a number.")
    assert_equal(state.calculation_count, 1)

    state = make_state()
    calculate_grams_to_moles(state, "Fe", "111.69")
    assert_equal(state.result, "2.0 moles")
    assert_equal(state.last_tool, "Grams to Moles (Fe)")
    calculate_grams_to_moles(state, "Xx", "1")
    assert_equal(state.result, "Not a valid element.")
    assert_equal(state.calculation_count, 1)

    state = make_state()
    calculate_enthalpy(state, METHANE, "1", "", OXYGEN, "2", "",
                       CARBON_DIOXIDE, "1", "", WATER, "2", "")
    assert_equal(state.result, "ΔH total = -890.3 kJ")
    assert_equal(state.last_tool, "Enthalpy")
    calculate_enthalpy(state, CUSTOM_COMPOUND, "1", "-100", NO_COMPOUND, "",
                       "", CARBON_DIOXIDE, "1", "", NO_COMPOUND, "", "")
    assert_equal(state.result, "ΔH total = -293.5 kJ")
    assert_equal(state.calculation_count, 2)
    calculate_enthalpy(state, CUSTOM_COMPOUND, "1", "", NO_COMPOUND, "", "",
                       CARBON_DIOXIDE, "1", "", NO_COMPOUND, "", "")
    assert_equal(state.result,
                 "Reactants and product enthalpies need to be a number")
    calculate_enthalpy(state, METHANE, "x", "", NO_COMPOUND, "", "",
                       CARBON_DIOXIDE, "1", "", NO_COMPOUND, "", "")
    assert_equal(state.result,
                 "Reactants and product coefficients need to be a number")
    calculate_enthalpy(state, NO_COMPOUND, "", "", NO_COMPOUND, "", "",
                       CARBON_DIOXIDE, "1", "", NO_COMPOUND, "", "")
    assert_equal(state.result, "Choose at least one reactant and one product.")
    calculate_enthalpy(state, METHANE, "1", "", NO_COMPOUND, "", "",
                       NO_COMPOUND, "", "", NO_COMPOUND, "", "")
    assert_equal(state.result, "Choose at least one reactant and one product.")
    assert_equal(state.calculation_count, 2)


def test_results_route() -> None:
    """Tests the results route with an empty and a filled history."""
    state = make_state()
    assert_equal(results(state), Page(state, [
        Header("📋 Previous Results"),
        "Total calculations: 0",
        "Last tool used: None yet",
        "Nothing calculated yet.",
        Button("Home", index),
    ]))
    state = State(ELEMENTS, [Result("Enthalpy", "ΔH total = 1 kJ")],
                  "", 1, "Enthalpy", "All elements", False, [])
    assert_equal(results(state), Page(state, [
        Header("📋 Previous Results"),
        "Total calculations: 1",
        "Last tool used: Enthalpy",
        Table([["Tool used", "Result"], ["Enthalpy", "ΔH total = 1 kJ"]]),
        Button("Home", index),
    ]))


def test_settings() -> None:
    """Tests the select box and check box features."""
    sample = [element("H", 1.008, 1), element("Ca", 40.078, 20),
              element("Sc", 44.956, 21)]
    assert_equal(filter_library(sample, "All elements"), sample)
    assert_equal(filter_library(sample, "1-20"), [sample[0], sample[1]])
    assert_equal(filter_library(sample, "21-54"), [sample[2]])
    assert_equal(filter_library(sample, "55-86"), [])
    assert_equal(filter_library(sample, "not a range"), sample)

    assert_equal(format_number(111.69, False), "111.69")
    assert_equal(format_number(111.69, True), "112")
    assert_equal(format_number(2.0000000000000004, True), "2")
    assert_equal(format_number(-890.3, True), "-890")
    assert_equal(format_number(0.0, True), "0")

    state = make_state()
    show_library_section(state, "21-54")
    assert_equal(state.library_section, "21-54")
    small = State(sample, [], "", 0, "None yet", "21-54", False, [])
    assert_equal(element_library(small), Page(small, [
        Button("Home", index),
        Header("📖 Element Library"),
        "Atomic number range to show:",
        SelectBox("section", LIBRARY_SECTIONS, "21-54"),
        Button("Show", show_library_section),
        Table([["Elements", "Molar mass", "Atomic #"],
               ["Sc", "44.956", "21"]]),
    ]))

    set_rounding(state, True)
    assert_equal(state.round_up, True)
    set_rounding(state, False)
    assert_equal(state.round_up, False)

    assert_equal(moles_to_mass_converter("Fe", "2", ELEMENTS, True),
                 "112 grams")
    assert_equal(mass_to_moles_converter("Fe", "111.69", ELEMENTS, True),
                 "2 moles")
    assert_equal(mass_to_moles_converter("Fe", "120", ELEMENTS, True),
                 "3 moles")
    assert_equal(enthalpy_calculator("-74.8", "1", "0", "2", "-393.5", "1",
                                     "-285.8", "2", True),
                 "ΔH total = -890 kJ")

    state = make_state()
    set_rounding(state, True)
    calculate_moles_to_grams(state, "Fe", "2")
    assert_equal(state.result, "112 grams")
    calculate_grams_to_moles(state, "Fe", "111.69")
    assert_equal(state.result, "2 moles")
    calculate_enthalpy(state, METHANE, "1", "", OXYGEN, "2", "",
                       CARBON_DIOXIDE, "1", "", WATER, "2", "")
    assert_equal(state.result, "ΔH total = -890 kJ")
    assert_equal(state.calculation_count, 3)


def test_try_setup() -> None:
    """Tests that styling steps are skipped safely when unavailable."""
    assert_equal(try_setup(lambda: None), True)
    assert_equal(try_setup(lambda: missing_drafter_helper()), False)
    assert_equal(try_setup(lambda: len(5)), False)


def test_enthalpy_library() -> None:
    """Tests the compound helpers and the new ΔH library and help pages."""
    water = Compound("H2O", "Water (liquid)", -285.8)
    carbon = Compound("C", "Carbon, graphite (solid)", 0.0)
    assert_equal(compound_label(water), "H2O - Water (liquid)")
    assert_equal(compound_options([water, carbon]),
                 [NO_COMPOUND, CUSTOM_COMPOUND, "H2O - Water (liquid)",
                  "C - Carbon, graphite (solid)"])
    assert_equal(find_compound("H2O - Water (liquid)", [water, carbon]), water)
    assert_equal(find_compound("C - Carbon, graphite (solid)", [water, carbon]),
                 carbon)
    assert_equal(find_compound("Xx - Nothing", [water, carbon]), None)
    assert_equal(read_slot(NO_COMPOUND, "5", "7", [water]), ["0", "0"])
    assert_equal(read_slot(CUSTOM_COMPOUND, " 2 ", " -50 ", [water]),
                 ["-50", "2"])
    assert_equal(read_slot("H2O - Water (liquid)", "2", "", [water]),
                 ["-285.8", "2"])
    assert_equal(read_slot("Xx - Nothing", "2", "", [water]), ["", "2"])
    assert_equal(find_compound(METHANE, COMPOUNDS).enthalpy, -74.8)
    assert_equal(find_compound(OXYGEN, COMPOUNDS).enthalpy, 0.0)
    choices = [NO_COMPOUND, "a", "b"]
    assert_equal(slot_inputs("Reactant 1:", "reactant_1", choices), [
        "Reactant 1:",
        SelectBox("reactant_1", choices, NO_COMPOUND),
        "Coefficient (the number in front of it in the balanced equation):",
        TextBox("reactant_1_coefficient", ""),
        "Custom ΔH in kJ/mol (only if you chose 'Custom ΔH value'):",
        TextBox("reactant_1_custom", ""),
    ])

    small = State([], [], "", 0, "None yet", "All elements", False,
                  [water, carbon])
    assert_equal(enthalpy_library(small), Page(small, [
        Button("Home", index),
        Header("📚 ΔH Library"),
        "Standard enthalpies of formation at 25 °C, in kJ/mol. Elements in "
        "their standard state (like O2 and H2) are 0. Values are rounded and "
        "can differ slightly between textbooks.",
        Button("🔥 Go to the Enthalpy Calculator", enthalpy),
        Table([["Formula", "Name", "ΔH of formation (kJ/mol)"],
               ["H2O", "Water (liquid)", "-285.8"],
               ["C", "Carbon, graphite (solid)", "0.0"]]),
    ]))
    assert_equal(instructions(small), Page(small, [
        Header("❓ Instructions")] + INSTRUCTION_LINES + [
        Button("Home", index),
    ]))


def run_all_tests() -> None:
    """Runs every unit test above."""
    test_converters()
    test_enthalpy()
    test_formulas()
    test_save_result()
    test_display_routes()
    test_page_routes()
    test_calculate_routes()
    test_results_route()
    test_settings()
    test_try_setup()
    test_enthalpy_library()


run_all_tests()
style_website()
start_server(State(ELEMENTS, [], "", 0, "None yet", "All elements", False,
                   COMPOUNDS))
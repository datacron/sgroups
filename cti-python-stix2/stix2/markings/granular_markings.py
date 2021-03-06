"""Functions for working with STIX 2.0 granular markings.
"""

from stix2 import exceptions
from stix2.markings import utils
from stix2.utils import new_version


def get_markings(obj, selectors, inherited=False, descendants=False):
    """
    Get all markings associated to with the properties.

    Args:
        obj: An SDO or SRO object.
        selectors: string or list of selector strings relative to the SDO or
            SRO in which the properties appear.
        inherited: If True, include markings inherited relative to the
            properties.
        descendants: If True, include granular markings applied to any children
            relative to the properties.

    Raises:
        InvalidSelectorError: If `selectors` fail validation.

    Returns:
        list: Marking identifiers that matched the selectors expression.

    """
    selectors = utils.convert_to_list(selectors)
    utils.validate(obj, selectors)

    granular_markings = obj.get("granular_markings", [])

    if not granular_markings:
        return []

    results = set()

    for marking in granular_markings:
        for user_selector in selectors:
            for marking_selector in marking.get("selectors", []):
                if any([(user_selector == marking_selector),  # Catch explicit selectors.
                        (user_selector.startswith(marking_selector) and inherited),  # Catch inherited selectors.
                        (marking_selector.startswith(user_selector) and descendants)]):  # Catch descendants selectors
                    refs = marking.get("marking_ref", [])
                    results.update([refs])

    return list(results)


def set_markings(obj, marking, selectors):
    """
    Removes all markings associated with selectors and appends a new granular
    marking. Refer to `clear_markings` and `add_markings` for details.

    Args:
        obj: An SDO or SRO object.
        selectors: string or list of selector strings relative to the SDO or
            SRO in which the properties appear.
        marking: identifier or list of marking identifiers that apply to the
            properties selected by `selectors`.

    Returns:
        A new version of the given SDO or SRO with specified markings removed
        and new ones added.

    """
    obj = clear_markings(obj, selectors)
    return add_markings(obj, marking, selectors)


def remove_markings(obj, marking, selectors):
    """
    Removes granular_marking from the granular_markings collection.

    Args:
        obj: An SDO or SRO object.
        selectors: string or list of selectors strings relative to the SDO or
            SRO in which the properties appear.
        marking: identifier or list of marking identifiers that apply to the
            properties selected by `selectors`.

    Raises:
        InvalidSelectorError: If `selectors` fail validation.
        MarkingNotFoundError: If markings to remove are not found on
            the provided SDO or SRO.

    Returns:
        A new version of the given SDO or SRO with specified markings removed.

    """
    selectors = utils.convert_to_list(selectors)
    marking = utils.convert_to_marking_list(marking)
    utils.validate(obj, selectors)

    granular_markings = obj.get("granular_markings")

    if not granular_markings:
        return obj

    granular_markings = utils.expand_markings(granular_markings)

    to_remove = []
    for m in marking:
        to_remove.append({"marking_ref": m, "selectors": selectors})

    remove = utils.build_granular_marking(to_remove).get("granular_markings")

    if not any(marking in granular_markings for marking in remove):
        raise exceptions.MarkingNotFoundError(obj, remove)

    granular_markings = [
        m for m in granular_markings if m not in remove
    ]

    granular_markings = utils.compress_markings(granular_markings)

    if granular_markings:
        return new_version(obj, granular_markings=granular_markings)
    else:
        return new_version(obj, granular_markings=None)


def add_markings(obj, marking, selectors):
    """
    Appends a granular_marking to the granular_markings collection.

    Args:
        obj: An SDO or SRO object.
        selectors: list of type string, selectors must be relative to the TLO
            in which the properties appear.
        marking: identifier or list of marking identifiers that apply to the
            properties selected by `selectors`.

    Raises:
        InvalidSelectorError: If `selectors` fail validation.

    Returns:
        A new version of the given SDO or SRO with specified markings added.

    """
    selectors = utils.convert_to_list(selectors)
    marking = utils.convert_to_marking_list(marking)
    utils.validate(obj, selectors)

    granular_marking = []
    for m in marking:
        granular_marking.append({"marking_ref": m, "selectors": sorted(selectors)})

    if obj.get("granular_markings"):
        granular_marking.extend(obj.get("granular_markings"))

    granular_marking = utils.expand_markings(granular_marking)
    granular_marking = utils.compress_markings(granular_marking)
    return new_version(obj, granular_markings=granular_marking)


def clear_markings(obj, selectors):
    """
    Removes all granular_markings associated with the selectors.

    Args:
        obj: An SDO or SRO object.
        selectors: string or list of selectors strings relative to the SDO or
            SRO in which the properties appear.

    Raises:
        InvalidSelectorError: If `selectors` fail validation.
        MarkingNotFoundError: If markings to remove are not found on
            the provided SDO or SRO.

    Returns:
        A new version of the given SDO or SRO with specified markings cleared.

    """
    selectors = utils.convert_to_list(selectors)
    utils.validate(obj, selectors)

    granular_markings = obj.get("granular_markings")

    if not granular_markings:
        return obj

    granular_markings = utils.expand_markings(granular_markings)

    sdo = utils.build_granular_marking(
        [{"selectors": selectors, "marking_ref": "N/A"}]
    )

    clear = sdo.get("granular_markings", [])

    if not any(clear_selector in sdo_selectors.get("selectors", [])
               for sdo_selectors in granular_markings
               for clear_marking in clear
               for clear_selector in clear_marking.get("selectors", [])
               ):
        raise exceptions.MarkingNotFoundError(obj, clear)

    for granular_marking in granular_markings:
        for s in selectors:
            if s in granular_marking.get("selectors", []):
                marking_refs = granular_marking.get("marking_ref")

                if marking_refs:
                    granular_marking["marking_ref"] = ""

    granular_markings = utils.compress_markings(granular_markings)

    if granular_markings:
        return new_version(obj, granular_markings=granular_markings)
    else:
        return new_version(obj, granular_markings=None)


def is_marked(obj, marking=None, selectors=None, inherited=False, descendants=False):
    """
    Checks if field is marked by any marking or by specific marking(s).

    Args:
        obj: An SDO or SRO object.
        selectors: string or list of selectors strings relative to the SDO or
            SRO in which the properties appear.
        marking: identifier or list of marking identifiers that apply to the
            properties selected by `selectors`.
        inherited: If True, return markings inherited from the given selector.
        descendants: If True, return granular markings applied to any children
            of the given selector.

    Raises:
        InvalidSelectorError: If `selectors` fail validation.

    Returns:
        bool: True if ``selectors`` is found on internal SDO or SRO collection.
            False otherwise.

    Note:
        When a list of marking identifiers is provided, if ANY of the provided
        marking identifiers match, True is returned.

    """
    if selectors is None:
        raise TypeError("Required argument 'selectors' must be provided")

    selectors = utils.convert_to_list(selectors)
    marking = utils.convert_to_marking_list(marking)
    utils.validate(obj, selectors)

    granular_markings = obj.get("granular_markings", [])

    marked = False
    markings = set()

    for granular_marking in granular_markings:
        for user_selector in selectors:
            for marking_selector in granular_marking.get("selectors", []):

                if any([(user_selector == marking_selector),  # Catch explicit selectors.
                        (user_selector.startswith(marking_selector) and inherited),  # Catch inherited selectors.
                        (marking_selector.startswith(user_selector) and descendants)]):  # Catch descendants selectors
                    marking_ref = granular_marking.get("marking_ref", "")

                    if marking and any(x == marking_ref for x in marking):
                        markings.update([marking_ref])

                    marked = True

    if marking:
        # All user-provided markings must be found.
        return markings.issuperset(set(marking))

    return marked

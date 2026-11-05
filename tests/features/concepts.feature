Feature: Classes and concepts get pages at their PDC codes, and the classification a browse page
  A family (publet spec Section 5.9.1) defines the classes directly under one
  class together, and its page has a place for each. A class's code lands on
  that place. A concept is a definition whose name is its PDC code. Its page
  shows its form, boundary, place in the classification, members, the
  calculations that solve it, its versions and the expert group covering it,
  and links to review it. Every page says whether its object's author signed
  it. Pages need no script.

  Background:
    Given the reading bundles of the PDC sample

  Scenario: A quantity concept's page shows its boundary, members and versions
    When I build the site with the sustenaut theme
    Then it succeeds
    And the page for "628.9~1" says "Indoor shelves or racks lit only by LEDs"
    And the page for "628.9~1" says "Electricity for lights, fans and pumps"
    And the page for "628.9~1" lists both extracts as members
    And the page for "628.9~1" says "Versions · 2"

  Scenario: A code two concepts claim is shown as contested, with both
    When I build the site with the sustenaut theme
    Then the page for "628.9~1" says "Contested code."
    And the page for "628.9~1" says "Indoor plant lighting electricity"

  Scenario: A relation concept's page shows its slots and the ways to compute it
    When I build the site with the sustenaut theme
    Then the page for "628.9~2" says "any one slot is computed from all the others"
    And the page for "628.9~2" says "Ways to compute it · 1"
    And the page for "628.9~2" says "solves <code>energy</code> from <code>power</code>"

  Scenario: A concept under an expert group's code shows the group
    When I build the site with the sustenaut theme
    Then the page for "628.9~2" says "Expert group"
    And the page for "628.9~2" says "2 stewards"

  Scenario: A code with a slash is served with an underscore
    When I build the site with the sustenaut theme
    Then the page for "631/635" says "Farm management. Agronomy. Horticulture"

  Scenario: The classification is browsed from the top tables down
    When I build the site with the sustenaut theme
    Then the classification page lists "631.5" under "631" under "631/635"
    And the classification page lists "628.9~2" under "628.9" under "628"

  Scenario: A class's code lands on its place in its family's page
    When I build the site with the sustenaut theme
    Then the page for "631" lands on "631" in the family under "631/635"
    And the family under "631/635" has a place for "631"
    And the family under "631/635" has a place for "633/635"

  Scenario: A family's page names the classes above it, from the top down
    When I build the site with the sustenaut theme
    Then the family under "631/635" names "----", "6", "63" and "631/635" above it in that order

  Scenario: A family's page links the family under each class that has one
    When I build the site with the sustenaut theme
    Then the family under "631/635" links the family under "631"
    And the family under "631/635" links the family under "633/635"

  Scenario: A concept placed in a family's class names that class as broader
    When I build the site with the sustenaut theme
    Then the page for "628.9~2" says "Broader · 1"
    And the page for "628.9~2" links "628.9" in the family under "628"

  Scenario Outline: Every page says whether its object's author signed it
    Given the family under "631/635" has the signature status "<status>"
    When I build the site with the sustenaut theme
    Then the family under "631/635" says "<tag>"
    And the family under "631/635" says "<meaning>"
    And the page for "631" says "<tag>"

    Examples:
      | status   | tag                       | meaning                                 |
      | verified | signed by its author      | the signature verifies: it counts       |
      | missing  | unsigned                  | counts for nothing until its author signs it |
      | invalid  | signature does not verify | it does not verify: it counts for nothing |

  Scenario: An extract's page names its concept and links its suggestion for review
    When I build the site with the sustenaut theme
    Then the Gargaro extract's page names the concept "628.9~1"
    And the Gargaro extract's page links its suggestion at "https://review.sustenaut.eu/s/"

  Scenario: Concept pages carry no script
    When I build the site with the sustenaut theme
    Then no page for a concept holds a script

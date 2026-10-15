Feature: Concepts get pages at their PDC codes, and the classification a browse page
  A concept (publet spec Section 5.9.1) is a definition whose name is its
  PDC code. Its page shows its form, boundary, place in the classification,
  members, the calculations that solve it, its versions and the expert group
  covering it, and links to review it. Pages need no script.

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

  Scenario: An extract's page names its concept and links its suggestion for review
    When I build the site with the sustenaut theme
    Then the Gargaro extract's page names the concept "628.9~1"
    And the Gargaro extract's page links its suggestion at "https://review.sustenaut.eu/s/"

  Scenario: Concept pages carry no script
    When I build the site with the sustenaut theme
    Then no page for a concept holds a script

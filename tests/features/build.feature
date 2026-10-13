Feature: A theme turns publet reading bundles into a static website
  `pubtheme build` reads the bundles `pub bundle` wrote and writes a page per
  object and per name with the chosen theme. The bundles decide what a page
  shows; the theme decides only how it looks.

  Background:
    Given the reading bundles of publication 0

  Scenario: Every object and every name gets a page
    When I build the site with the sustenaut theme
    Then it succeeds
    And every object in the bundles has a page
    And the name "{tray}" has a page
    And the index links every claim's page
    And the site has a stylesheet carrying the theme's colours

  Scenario: Each page can be checked against its object
    When I build the site with the sustenaut theme
    Then every object's canonical bytes are copied unchanged
    And every object's reading bundle is copied beside its page

  Scenario: A claim's page shows where it sits
    When I build the site with the sustenaut theme
    Then the tray energy claim's page links the tray dimension as its unit
    And the tray energy claim's page links the claim computed from it

  Scenario: A value not yet gathered reads as not yet known
    When I build the site with the sustenaut theme
    Then the tray energy claim's page says "not yet known"

  Scenario: A quantity reads in its measure's order
    Given the tray energy claim holds an estimate with high, likely and low
    When I build the site with the sustenaut theme
    Then the tray energy claim's page shows low, likely and high in that order

  Scenario: Text from an object is shown as text, never as markup
    Given the tray energy claim's content holds markup
    When I build the site with the sustenaut theme
    Then the tray energy claim's page shows the markup escaped

  Scenario: The host's settings name the site
    Given a site settings file titling the site "Sustenaut publications"
    When I build the site with those settings
    Then it succeeds
    And the index is titled "Sustenaut publications"

  Scenario: The themes this package holds are listed
    When I list the themes
    Then it succeeds
    And it prints "sustenaut"

  Scenario: An unknown theme is refused
    When I build the site with a theme named "nonesuch"
    Then it fails
    And stderr mentions "no theme named nonesuch"

  Scenario: Bundles of a shape this release cannot read are refused
    Given the bundles say they are version 99
    When I build the site with the sustenaut theme
    Then it fails
    And stderr mentions "bundle version 99"

  Scenario: The site is never written over an earlier one
    Given the site directory already holds a file
    When I build the site with the sustenaut theme
    Then it fails
    And stderr mentions "is not empty"

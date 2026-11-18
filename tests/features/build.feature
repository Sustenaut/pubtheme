Feature: A theme turns publet reading bundles into a static website
  `pubtheme build` reads the bundles `pub bundle` wrote and writes a page per
  object and per name with the chosen theme. The bundles decide what a page
  shows; the theme decides only how it looks.

  Background:
    Given a scratch directory
    And the program under test is "pubtheme"
    And a file "bundles" copied from "tests/testdata/publication-0"

  Scenario: Every object and every name gets a page
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then it succeeds
    And every object in the bundles has a page
    And the name "{tray}" has a page
    And the index links every claim's page
    And the file "site/style.css" includes "--color-ground"
    And the file "site/style.css" includes "#f3efe2"

  Scenario: Each page can be checked against its object
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then every object's canonical bytes are copied unchanged
    And every object's reading bundle is copied beside its page

  Scenario: A claim's page shows where it sits
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then the tray energy claim's page links the tray dimension as its unit
    And the tray energy claim's page links the claim computed from it

  Scenario: A value not yet gathered reads as not yet known
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then the tray energy claim's page says "not yet known"

  Scenario: A quantity reads in its measure's order
    Given the tray energy claim holds an estimate with high, likely and low
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then the tray energy claim's page shows low, likely and high in that order

  Scenario: Text from an object is shown as text, never as markup
    Given the tray energy claim's content holds markup
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then the tray energy claim's page shows the markup escaped

  Scenario: The host's settings name the site
    Given a file "site.json" holding:
      """
      {"title": "Sustenaut publications"}
      """
    When I run "pubtheme build --bundles=bundles --out=site --site=site.json"
    Then it succeeds
    And the file "site/index.html" includes "<title>Sustenaut publications</title>"

  Scenario: The themes this package holds are listed
    When I run "pubtheme themes"
    Then it succeeds
    And it prints "sustenaut"

  Scenario: An unknown theme is refused
    When I run "pubtheme build --bundles=bundles --out=site --theme=nonesuch"
    Then it fails
    And stderr mentions "no theme named nonesuch"

  Scenario: Bundles of a shape this release cannot read are refused
    Given the bundles say they are version 99
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then it fails
    And stderr mentions "bundle version 99"

  Scenario: The site is never written over an earlier one
    Given a file "site/old.html" holding "an earlier page"
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    Then it fails
    And stderr mentions "is not empty"

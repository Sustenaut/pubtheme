Feature: Objects kept elsewhere are rendered on request
  A host limits how many files a site can have. `pubtheme build --external=DIR --worker-out=DIR` leaves the
  objects of another bundle, and the names only they define, out of the site, and writes what a site's
  server needs to render their pages on request: an index, and the templates compiled for a Worker.

  Background:
    Given a scratch directory
    And the program under test is "pubtheme"
    And a file "bundles" copied from "tests/testdata/concepts"
    And a file "kept" copied from "tests/testdata/concepts"

  Scenario: They get no files, and read the same when rendered
    When I run "pubtheme build --bundles=bundles --out=site --theme=sustenaut"
    And I run "pubtheme build --bundles=bundles --out=elsewhere --external=kept --worker-out=worker"
    Then it succeeds
    And that site has no page, bundle or bytes for those objects
    And that site has no page for the names only they define
    And every name's rendered page is the page the whole site has
    And every object's rendered page is the page the whole site has

  Scenario: The index names the family each class's code is defined in
    When I run "pubtheme build --bundles=bundles --out=elsewhere --external=kept --worker-out=worker"
    Then the index entry for "631" names the family under "631/635"

  Scenario: A code's class comes first when searching, and words find classes
    When I run "pubtheme build --bundles=bundles --out=elsewhere --external=kept --worker-out=worker"
    Then a search for "628.9" finds "628.9" first
    And a search for "rural engineering" finds nothing that lacks those words

  Scenario: Keeping objects elsewhere needs somewhere to write the renderer
    When I run "pubtheme build --bundles=bundles --out=elsewhere --external=kept"
    Then it fails
    And stderr mentions "--external and --worker-out go together"

  Scenario: The search page escapes what was asked
    When I run "pubtheme build --bundles=bundles --out=elsewhere --external=kept --worker-out=worker"
    Then a search page for "<script>" shows it escaped

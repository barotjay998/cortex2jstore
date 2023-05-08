# Configure the columns to be matched between Cortex and JStore
# NOTE: The key is the JStore column name and the value is the Cortex column name

match_columns = {
    # Cortex column name: JStore column name
    "Title[2071407]": "Title",
    "Description[2071422]": "Description / Data",
    "Source[2071436]": "Notes",
    "Date[2071410]": "Date Circa",
    "Precise Date[2071412]": "Date Created",
    "Photographer[2071421]": "Source Name",
    "Vanderbilt Local Subjects[2083876]": "Tags",
    "Vanderbilt People[2083840]": "Person Shown",
    "Format[2071431]": "Original Asset Type",
    # Work Type is in this case will be used to 
    # represent the physical condtion of the asset.
    "Work Type[2071442]": "Original Asset Condition",
    "Contributor[2071404]": "Asset Donor",
    # "Copyright[2071426]": "Copyright",
    # "Holding Institution[2071428]": "Vu Archive Collection",
    # Cortex Unique ID
    "Identifier[2071405]": "Unique Identifier",
    "Edition[2071419]": "Date Scanned"

    # Add more columns here
}

jstore_schema_columns = {
    "Vanderbilt Local Subjects[2083876]",
    "Vanderbilt People[2083840]",
}

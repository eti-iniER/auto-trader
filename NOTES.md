# Notes

Hi,

I like to add a `NOTES.md` file to my freelance projects to keep track of any gotchas in the codebase, or any other information I'd like a future developer (possibly myself) to be aware of. I also use it to track my progress throughout development. This is meant to be a more technical and detail-focused counterpart to the `README.md` file that is standard across all projects.

## Backend

### Alert validation and order fulfillment

-   Order fulfillment is handled in the `order_fulfillment.py` file. It handles the situation where an order isn't converted into a trade within X minutes, and deletes it. It also deletes our mirror "Order" model in the DB, which is used to track an app-created order

-   Alerts are primarily handled in the `core` service: payload parsing, executing a trade, computing the values for an automatic trade, etc. Validation is also taken care of here, in the `core/payload_validator.py` file.

### File processing

-   The CSV tends to have a weird empty symbol in front of the Symbol header - Make sure to remember to remove that

## Frontend

The frontend is pretty straightforward. Here are some quirks you might need to be aware of:

### Revivers

I've set up the API client such that it parses Decimals and ISO datetime strings into Number and Date types respectively. I do this for convenience, since it is easier than having to deal with conversion each time these values are used. It is also intuitive once you are aware that it is happening.

To modify which fields are converted to Decimal and Date, you can modify the `lib/revivers.ts` file.

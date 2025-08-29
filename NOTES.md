# Notes

Hi future dev,

I like to add this `NOTES.md` file to my freelance projects to keep track of any gotchas in the codebase, or any other information I'd like a future developer (possibly myself) to be aware of. I also use it to track my progress throughout development. This is meant to be a more technical and detail-focused counterpart to the [`README.md`](./README.md) file that is standard across all projects.

## Backend

### Alert validation and order fulfillment

-   Order fulfillment is handled in the [`order_fulfillment.py`](./backend/app/services/order_fulfillment.py) file. It handles the situation where an order isn't converted into a trade within X minutes, and deletes it. It also deletes our mirror "Order" model in the DB, which is used to track an app-created order

-   Alerts are primarily handled in the [`trading`](./backend/app/services/trading/) service: payload parsing, executing a trade, computing the values for an automatic trade, etc. Validation is also taken care of here, in the [`trading/payload_validator.py`](./backend/app/services/trading/payload_validator.py) file.

-   To implement the specification to avoid creating orders for the same instrument within 8 hours of each other, I decided to use an Order model in the DB, which is analogous to IG's Working Order model. Whenever we create a working order on IG, we create a corresponding Order model, which is used to track fulfillment. We run a frequent job on the background to delete orders which exceed this threshold.

    To fulfill this specification, we then simply have to check if an Order exists in the DB for the given Instrument.

-   The [`CreateWorkingOrderRequest`](./backend/app/clients/ig/types.py#242) type has an `expiry` field set to a magic constant of `DEC-27`; IG uses this value as well when making requests from their dashboard. I believe this means the order expires in December, 2027, and is just a placeholder for "a faraway date". Keep this in mind if anything weird starts happening around that though.

### File processing

-   The CSV tends to have a weird empty symbol in front of the Symbol header - Make sure to remember to correct that

## Frontend

The frontend is pretty straightforward. Here are some quirks you might need to be aware of:

### Revivers

I've set up the API client such that it parses Decimals and ISO datetime strings into Number and Date types respectively. I do this for convenience, since it is easier than having to deal with conversion each time these values are used. It is also intuitive once you are aware that it is happening.

To modify which fields are converted to Decimal and Date, you can modify the [`lib/revivers.ts`](./frontend/src/lib/revivers.ts) file.

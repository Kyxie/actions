# Gas Price Tomorrow in Canada

This is a bot for checking tomorrow's gas price in Canada

## How to run

### Locally

- If you want to run locally, make sure install Python 3.10 and the libraries

  ```bash
  pip install requests
  ```

- Configure environment variables:
  - `SENDER_EMAIL`: sender address on a domain verified with Resend
  - `SENDER_PASS`: Resend API key
  - `USERS`: JSON array of recipients with `name`, `city`, and `email` fields
  - Supported cities: https://gaswizard.ca/gas-price-predictions/

- Run

  ```bash
  python main.py
  ```

### GitHub Actions

- The workflow is `.github/workflows/gasprice-tracker.yml` at the repository root.
- Set the `USERNAME` Actions variable to the Resend verified sender address and the `PASSWORD` Actions secret to the Resend API key. The workflow also reads the `USERS` and `ENABLE_EMAIL` variables.

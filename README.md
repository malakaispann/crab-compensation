# Crab Compensation

An application that processes public-access data published by the State of Maryland regarding government payments to various entities.. Please see the [Data.gov catalog entry](catalog.data.gov/dataset/state-of-maryland-payments-data-fy2008-to-fy2020).

## Tech Stack
- [Python](https://www.python.org/) - The one and only
- [PySpark](https://spark.apache.org/docs/latest/api/python/index.html) - The Python wrapper for Apache Spark
- [UV](https://docs.astral.sh/uv/) - A package manager and build system for modern Python projects

## Use

### Local Development

1. Install UV using any methods listed on the [official docs](https://docs.astral.sh/uv/getting-started/installation/).
    * Also, install Make for shortcuts to common workflows
2. Update [dev.conf](dev.conf) as necessary.
    * See the [Environment Configuration section](#environment-configuration) for more details
3. Install dependencies using `make install-dev`
4. Make changes as necessary and test using `make test`
5. Run the application locally using `make start-local` to process the Maryland payments data for the year 2024 (configurable via the `--year` parameter)

#### Important Commands

```bash
make clean         # Remove build artifacts and virtual environment
make format        # Auto-format code
make install-dev   # Install all dependencies including dev tools
make install-prod  # Install only production dependencies
make lint-check    # Check code quality
make package       # Build both dependency zip and module wheel
make test          # Run the test suite
```

### AWS EMR Deployment
The application is designed to run on AWS EMR clusters with pre-installed Spark. To deploy:

1. Build the deployment artifacts:
   ```bash
   make package
   ```
   This creates two files in the `dist/` directory:
   - `dependencies.zip` - Contains all production dependencies
   - `crab_compensation-0.0.0-py3-none-any.whl` - The application wheel file

2. Upload both files to S3:
   ```bash
   aws s3 cp dist/dependencies.zip s3://your-bucket/crab-compensation/
   aws s3 cp dist/crab_compensation-0.0.0-py3-none-any.whl s3://your-bucket/crab-compensation/
   ```
3. Upload the input data to S3:
    ```bash
    aws s3 cp data/State_of_Maryland_Payments_Data__FY2008_to_FY2024.csv.gz s3://your-bucket/crab-compensation/
    ```

4. Submit the job to EMR with appropriate Spark configurations pointing to these artifacts.

## Data

### Input Data
The application processes Maryland State payment data from the [State of Maryland Payments Dataset](https://catalog.data.gov/dataset/state-of-maryland-payments-data-fy2008-to-fy2020). Here's some information about the data:

- Coverage: State agency payments to private businesses, local governments, non-profit organizations, and individuals from FY2008 to FY2024. 
- Format: Compressed CSV file (`.csv.gz`)
- **Available Data**:

| Column          | Type              | Description                                   |
|-----------------|-------------------|-----------------------------------------------|
| `Fiscal Year`   | Integer           | The fiscal year of the payment                |
| `Agency Name`   | String            | Name of the paying agency                     |
| `Vendor Name`   | String            | Name of the payment recipient                 |
| `Vendor Zip`    | String (nullable) | Vendor's ZIP code                             |
| `Amount`        | Double            | Payment amount                                |
| `Fiscal Period` | Integer           | The fiscal period within the year             |
| `Date`          | Timestamp         | Payment date (format: MM/dd/yyyy hh:mm:ss a)  |
| `Category`      | String            | Payment category                              |

### Output Data
The application generates a JSON file containing compensation analysis for a specified fiscal year.

#### JSON Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Compensation Analysis",
  "description": "Results of compensation analysis for a fiscal year",
  "type": "object",
  "properties": {
    "fiscalYear": {
      "description": "The fiscal year being analyzed",
      "type": "integer"
    },
    "totalAmount": {
      "description": "Total money paid",
      "type": "number"
    },
    "averageTransaction": {
      "description": "Average transaction amount",
      "type": "number"
    },
    "minTransaction": {
      "description": "Minimum transaction amount",
      "type": "number"
    },
    "maxTransaction": {
      "description": "Maximum transaction amount",
      "type": "number"
    },
    "transactionCount": {
      "description": "Total number of transactions",
      "type": "integer"
    },
    "topVendors": {
      "description": "Top 10 vendors by total amount paid",
      "type": "array",
      "items": {"$ref": "#/$defs/VendorSummary"}
    }
  },
  "required": [
    "fiscalYear",
    "totalAmount",
    "averageTransaction",
    "minTransaction",
    "maxTransaction",
    "transactionCount",
    "topVendors"
  ],
  "$defs": {
    "VendorSummary": {
      "title": "Vendor Summary",
      "description": "Summary of payments to a vendor",
      "type": "object",
      "properties": {
        "vendorName": {
          "description": "Name of the vendor",
          "type": "string"
        },
        "totalPaid": {
          "description": "Total amount paid to the vendor",
          "type": "number"
        },
        "transactionCount": {
          "description": "Number of transactions with the vendor",
          "type": "integer"
        }
      },
      "required": ["vendorName", "totalPaid", "transactionCount"]
    }
  }
}
```

#### Example Output
```json
{
  "fiscalYear": 2024,
  "totalAmount": 1234567890.50,
  "averageTransaction": 12345.67,
  "minTransaction": 0.01,
  "maxTransaction": 9876543.21,
  "transactionCount": 100000,
  "topVendors": [
    {
      "vendorName": "Example Vendor Inc",
      "totalPaid": 1234567.89,
      "transactionCount": 123
    },
    {
      "vendorName": "Another Company LLC",
      "totalPaid": 987654.32,
      "transactionCount": 89
    }
  ]
}
```

*Vendor list shortened for the sake of brevity.*

## Environment configuration

Configuration is managed through environment files. For local development, update the `dev.conf` file in the project root with required variables for data paths, output locations, and Java configuration.

**Important**: Spark requires Java 17 or earlier. Ensure your `JAVA_HOME` points to a compatible Java installation (see Local Development section).

## Quality Control


1. Code Formatting: Uses Black for consistent Python code formatting
   - Check formatting: `make format-check`
   - Apply formatting: `make format`

2. Linting: Uses Pylint for code quality analysis
   - Run linter: `make lint-check`

3. Testing: Uses Pytest
   - Run tests: `make test`


The project also uses GitHub Actions for continuous integration. All checks run automatically on pushes to the `dev` branch and on pull requests.

## Final Note

This project is not intended to be used as a template or guide, but it can definitely can be used as "inspiration." Please link back to this repo or [MalakaiSpann.com](https://malakaispann.com) if you do.
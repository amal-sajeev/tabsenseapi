# TabSense API

## Overview

TabSense is a comprehensive API for surface monitoring and management, designed to detect stains, manage schedules, camera links, and holiday tracking across multiple rooms and clients.

## Key Features

- **Stain Detection**: Automatically compare control and current images to identify surface stains
- **Schedule Management**: Create, update, and manage capture schedules for different rooms
- **Camera Link Management**: Add, retrieve, and manage camera links for different sectors and rooms
- **Holiday Tracking**: Add and manage holiday schedules that may impact monitoring

## Prerequisites

- Python 3.8+
- FastAPI
- PyMongo
- Stain Detection Module (staindet)
- MongoDB

## Installation

1. Clone the repository
2. Install required dependencies:
   ```bash
   pip install fastapi pymongo staindet pillow uvicorn
   ```

3. Set up MongoDB:
   - Ensure MongoDB is installed and running
   - Set the `mongocred` environment variable with your MongoDB credentials

## Environment Setup

- `mongocred`: MongoDB connection credentials
- Ensure image storage directories:
  - `imagedata/control/`
  - `imagedata/captures/`

## Main Endpoints

- `/detect`: Stain detection across room sectors
- `/report`: Retrieve detection reports
- `/entry`: Schedule management (add, update, delete)
- `/cam`: Camera link management
- `/holiday`: Holiday tracking and management

## Database Structure

The API uses MongoDB with collections structured by:
- `{client}-{room}`: Detection results
- `{client}-schedule`: Capture schedules
- `{client}-cams`: Camera links
- `{client}-holidays`: Holiday schedules

## Security

- Requires client identification for all operations
- Uses UUID for unique identifiers
- Supports granular filtering and management

## Deployment

Use Uvicorn or any ASGI server to run the FastAPI application:
```bash
uvicorn detectapi:app --reload
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

[Specify your license here]

## Contact

For more information, please contact [Your Contact Information]
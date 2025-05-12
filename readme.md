# ![TabSense Logo](tabsense%20logo%20(Custom).png)

# TabSense API

TabSense is an intelligent stain detection and surface monitoring system that automates hygiene checks across environments with precision. Built on FastAPI and MongoDB, it allows seamless capture scheduling, image comparison, and comprehensive reporting, making it ideal for large facilities, research labs, or anywhere cleanliness is non-negotiable.

## 🔍 Features

- **Stain Detection**  
  Upload control and current images of surfaces, and TabSense will identify differences—using borders and shapes for auto-cropping and context-aware comparison.

- **Smart Scheduling**  
  Define when and where to run inspections with flexible day/time scheduling across sectors and rooms.

- **Rich Reports**  
  Generate reports over date ranges for clients and rooms. Get full detection logs, image IDs, and metadata.

- **Camera Link Management**  
  Save and manage camera feeds tied to specific sectors in specific rooms.

- **Holiday Handling**  
  Define holiday periods to suppress detections during off-hours or inactive days.

## 🚀 Getting Started

### Requirements

Install the dependencies from the `requirements.txt` file:

```
pip install -r requirements.txt
```

Ensure your environment has access to a running MongoDB instance and set the required credentials as environment variables:

```
export mongocred=your_mongo_user:your_mongo_password
```

### Running the API

To launch the server:

```
uvicorn detectapi:app --reload
```

Make sure `detectapi.py` and your image directories (`imagedata/control`, `imagedata/captures`) are correctly placed.

## 🧩 Endpoint Structure

The API is structured into five core functional zones:

1. **Detection**  
   - `/detect`: Main endpoint for stain comparison. Requires control and current image UUIDs, sector list, and room identifiers.

2. **Reports**  
   - `/report`: Fetches all detection records within a time range for a given room and client.

3. **Schedules**  
   - `/entry/*`: Add, update, delete, and fetch scheduled entries that trigger image comparisons.

4. **Cameras**  
   - `/cam/*`: Add, update, delete, and get camera links tied to sectors and rooms.

5. **Holidays**  
   - `/holiday/*`: Define and manage blackout periods where captures should be suppressed.

Each endpoint uses clear, minimalistic schemas using Pydantic for type safety. MongoDB collections are scoped by client and room for isolation and scale.

## 🗂 Directory Layout

```
TabSense/
├── detectapi.py           # Main FastAPI app with all endpoints
├── requirements.txt       # Dependency list
├── tabsense logo (Custom).png
├── imagedata/
│   ├── control/           # Control (clean) images
│   └── captures/          # Current (live) images
```

## 💡 Why TabSense?

TabSense isn't just stain detection—it's preventive hygiene intelligence. Schedule checks, analyze trends, and integrate effortlessly with your infrastructure. Whether you're cleaning up messes or catching them before they start, TabSense keeps your surfaces accountable.

## 🧠 Built With

- **FastAPI** – Blazing-fast web framework
- **MongoDB** – Flexible document-based storage
- **PIL** – Image handling
- **Custom stain detection engine (`staindet`)**

## 📬 Feedback

Got ideas, issues, or contributions? Open a pull request or create an issue. Help us make surfaces smarter.

---

**Cleanliness isn't optional. Intelligence shouldn't be either.**
```

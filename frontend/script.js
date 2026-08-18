// =========================================================
// LOGIN CHECK
// =========================================================

const userId = localStorage.getItem("user_id");

if (!userId) {
    window.location.href = "register.html";
}

// =========================================================
// GLOBAL VARIABLES
// =========================================================

let solarChart = null;
let windChart = null;

let historicalSolarChart = null;
let historicalWindChart = null;

let map = null;
let marker = null;

// =========================================================
// SAVE SITE DETAILS AND ANALYZE
// =========================================================

async function saveSiteAndAnalyze() {

    const siteId =
        document.getElementById("siteId").value.trim();

    const siteName =
        document.getElementById("inputSiteName").value.trim();

    const latitude =
        parseFloat(
            document.getElementById("inputLatitude").value
        );

    const longitude =
        parseFloat(
            document.getElementById("inputLongitude").value
        );

    const landArea =
        parseFloat(
            document.getElementById("inputLandArea").value
        );

    const landType =
        document.getElementById("inputLandType").value;

    const message =
        document.getElementById("message");


    // =====================================================
    // VALIDATION
    // =====================================================

    if (!siteId) {
        message.innerText = "Please enter a Site ID.";
        return;
    }

    if (!siteName) {
        message.innerText = "Please enter Site Name.";
        return;
    }

    if (
        !Number.isFinite(latitude) ||
        latitude < -90 ||
        latitude > 90
    ) {
        message.innerText = "Please enter a valid Latitude.";
        return;
    }

    if (
        !Number.isFinite(longitude) ||
        longitude < -180 ||
        longitude > 180
    ) {
        message.innerText = "Please enter a valid Longitude.";
        return;
    }

    if (
        !Number.isFinite(landArea) ||
        landArea <= 0
    ) {
        message.innerText = "Please enter a valid Land Area.";
        return;
    }


    message.innerText =
        "Saving site information...";


    try {

        // =================================================
        // 1. GET EXISTING SITE
        // =================================================

        const getSiteUrl =
            `http://127.0.0.1:8000/sites/${siteId}`;

        const getResponse =
            await fetch(getSiteUrl);

        const existingSite =
            await getResponse.json();


        if (!getResponse.ok ||
            existingSite.status !== "success") {

            message.innerText =
                existingSite.message ||
                "Site not found.";

            return;
        }


        const oldSite =
            existingSite.site;


        // =================================================
        // 2. UPDATE SITE IN POSTGRESQL
        // =================================================

        const updateUrl =
            `http://127.0.0.1:8000/sites/${siteId}`;


        const updateData = {

            project_id:
                oldSite.project_id,

            site_name:
                siteName,

            latitude:
                latitude,

            longitude:
                longitude,

            region:
                oldSite.region || "User Selected Location",

            land_area:
                landArea,

            elevation:
                oldSite.elevation || 0,

            land_type:
                landType,

            ownership:
                oldSite.ownership || "Private"
        };


        const updateResponse =
            await fetch(
                updateUrl,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(updateData)
                }
            );


        const updateResult =
            await updateResponse.json();


        if (!updateResponse.ok ||
            updateResult.status !== "success") {

            message.innerText =
                updateResult.message ||
                "Could not update site.";

            return;
        }


        message.innerText =
            "Location updated. Fetching resource data...";


        // =================================================
        // 3. FETCH NASA POWER DATA
        // =================================================

        const weatherUrl =
            `http://127.0.0.1:8000/sites/${siteId}/fetch-weather`;


        const weatherResponse =
            await fetch(
                weatherUrl,
                {
                    method: "POST"
                }
            );


        const weatherResult =
            await weatherResponse.json();


        if (!weatherResponse.ok ||
            weatherResult.status !== "success") {

            message.innerText =
                weatherResult.message ||
                "Could not fetch resource data.";

            return;
        }


        message.innerText =
            "Resource data updated. Loading dashboard...";


        // =================================================
        // 4. LOAD EXISTING DASHBOARD
        // =================================================

        await loadDashboard();


    }
    catch (error) {

        console.error(
            "SAVE SITE ERROR:",
            error
        );

        message.innerText =
            "Could not connect to FastAPI.";

    }

}

// =========================================================
// LOAD DASHBOARD
// =========================================================

async function loadDashboard() {

    const siteId =
        document
            .getElementById("siteId")
            .value
            .trim();

    const message =
        document.getElementById("message");

    if (!siteId) {

        message.innerText =
            "Please enter a Site ID.";

        return;
    }

    message.innerText =
        "Loading dashboard...";

    try {

        // =================================================
        // DASHBOARD API
        // =================================================

        const dashboardUrl =
            `http://127.0.0.1:8000/sites/${siteId}/dashboard`;

        console.log(
            "Calling:",
            dashboardUrl
        );

        const response =
            await fetch(dashboardUrl);

        console.log(
            "HTTP status:",
            response.status
        );

        const data =
            await response.json();

        console.log(
            "Dashboard response:",
            data
        );

        if (!response.ok) {

            message.innerText =
                data.message ||
                "API request failed.";

            return;
        }

        if (data.status !== "success") {

            message.innerText =
                data.message ||
                "Dashboard data unavailable.";

            return;
        }


        // =================================================
        // WEATHER
        // =================================================

        const temperature =
            Number(
                data.weather.temperature
            );

        const currentWind =
            Number(
                data.weather.wind_speed
            );

        document
            .getElementById("temperature")
            .innerText =
            temperature.toFixed(2);

        document
            .getElementById("currentWind")
            .innerText =
            currentWind.toFixed(2);


        // =================================================
        // SOLAR
        // =================================================

        const ghi =
            Number(
                data.solar.ghi
            );

        const dni =
            Number(
                data.solar.dni
            );

        const dhi =
            Number(
                data.solar.dhi
            );

        const predictedGhi =
            Number(
                data.solar.predicted_ghi
            );

        document
            .getElementById("ghi")
            .innerText =
            ghi.toFixed(2);

        document
            .getElementById("dni")
            .innerText =
            dni.toFixed(2);

        document
            .getElementById("dhi")
            .innerText =
            dhi.toFixed(2);

        document
            .getElementById("predictedGhi")
            .innerText =
            predictedGhi.toFixed(2);


        // =================================================
        // WIND
        // =================================================

        const predictedWind =
            Number(
                data.wind.predicted_wind_speed
            );

        document
            .getElementById("windSpeed")
            .innerText =
            currentWind.toFixed(2);

        document
            .getElementById("predictedWind")
            .innerText =
            predictedWind.toFixed(2);


        // =================================================
        // DATE
        // =================================================

        document
            .getElementById("recordedDate")
            .innerText =
            data.recorded_date || "--";


        // =================================================
        // SOLAR POTENTIAL
        // =================================================

        let solarStatus;

        if (ghi >= 5) {

            solarStatus = "HIGH";

        }

        else if (ghi >= 3) {

            solarStatus = "MEDIUM";

        }

        else {

            solarStatus = "LOW";

        }

        document
            .getElementById("solarStatus")
            .innerText =
            solarStatus;


        // =================================================
        // WIND POTENTIAL
        // =================================================

        let windStatus;

        if (currentWind >= 6) {

            windStatus = "HIGH";

        }

        else if (currentWind >= 3) {

            windStatus = "MEDIUM";

        }

        else {

            windStatus = "LOW";

        }

        document
            .getElementById("windStatus")
            .innerText =
            windStatus;


        // =================================================
        // GET SITE INFORMATION
        // =================================================

        const site =
            await loadSiteLocation(siteId);


        // =================================================
        // LOAD HISTORICAL DATA
        // =================================================

        await loadHistoricalData(siteId);


        // =================================================
        // LAND SCORE
        // =================================================

        const landScore =
            calculateLandScore(site);


        // =================================================
        // SOLAR SCORE
        // =================================================

        const solarScore =
            calculateSolarScore(ghi);


        // =================================================
        // WIND SCORE
        // =================================================

        const windScore =
            calculateWindScore(currentWind);


        // =================================================
        // OVERALL SCORE
        // =================================================

        const overallScore =
            Math.round(
                (solarScore * 0.40) +
                (windScore * 0.40) +
                (landScore * 0.20)
            );


        // =================================================
        // DISPLAY SCORES
        // =================================================

        document
            .getElementById("solarScore")
            .innerText =
            solarScore;

        document
            .getElementById("windScore")
            .innerText =
            windScore;

        document
            .getElementById("landScore")
            .innerText =
            landScore;

        document
            .getElementById("overallScore")
            .innerText =
            overallScore;


        // =================================================
        // PROGRESS BARS
        // =================================================

        const solarProgress =
            document.getElementById(
                "solarProgress"
            );

        const windProgress =
            document.getElementById(
                "windProgress"
            );

        const landProgress =
            document.getElementById(
                "landProgress"
            );

        if (solarProgress) {

            solarProgress.style.width =
                solarScore + "%";

        }

        if (windProgress) {

            windProgress.style.width =
                windScore + "%";

        }

        if (landProgress) {

            landProgress.style.width =
                landScore + "%";

        }


        // =================================================
        // SCORE MESSAGE
        // =================================================

        let scoreMessage;

        if (overallScore >= 80) {

            scoreMessage =
                "Excellent site for renewable energy deployment.";

        }

        else if (overallScore >= 65) {

            scoreMessage =
                "Good potential for renewable energy deployment.";

        }

        else if (overallScore >= 50) {

            scoreMessage =
                "Moderate potential. Further analysis recommended.";

        }

        else {

            scoreMessage =
                "Low potential. Detailed site assessment required.";

        }

        document
            .getElementById("scoreMessage")
            .innerText =
            scoreMessage;


        // =================================================
        // RECOMMENDATION
        // =================================================

        let recommendation;

        if (
            solarStatus === "HIGH" &&
            windStatus === "HIGH"
        ) {

            recommendation =
                "Excellent location for Hybrid Solar + Wind deployment.";

        }

        else if (
            solarStatus === "HIGH" &&
            windStatus === "MEDIUM"
        ) {

            recommendation =
                "Strong Solar potential with moderate Wind potential. Solar deployment is recommended.";

        }

        else if (
            solarStatus === "MEDIUM" &&
            windStatus === "HIGH"
        ) {

            recommendation =
                "Strong Wind potential with moderate Solar potential. Wind deployment is recommended.";

        }

        else if (
            solarStatus === "HIGH"
        ) {

            recommendation =
                "Good location for Solar deployment.";

        }

        else if (
            windStatus === "HIGH"
        ) {

            recommendation =
                "Good location for Wind deployment.";

        }

        else if (
            solarStatus === "MEDIUM" &&
            windStatus === "MEDIUM"
        ) {

            recommendation =
                "Suitable for Hybrid Solar + Wind deployment.";

        }

        else {

            recommendation =
                "Further site analysis is recommended.";

        }

        document
            .getElementById("recommendation")
            .innerText =
            recommendation;


        // =================================================
        // CURRENT SOLAR CHART
        // =================================================

        createSolarChart(
            ghi,
            dni,
            dhi,
            predictedGhi
        );


        // =================================================
        // CURRENT WIND CHART
        // =================================================

        createWindChart(
            currentWind,
            predictedWind
        );


        // =================================================
        // SUCCESS
        // =================================================

        message.innerText =
            "Dashboard loaded successfully!";

    }

    catch (error) {

        console.error(
            "ERROR:",
            error
        );

        message.innerText =
            "Could not connect to FastAPI.";

    }

}


// =========================================================
// SOLAR SCORE
// =========================================================

function calculateSolarScore(ghi) {

    if (ghi >= 6) {

        return 100;

    }

    else if (ghi >= 5) {

        return 90;

    }

    else if (ghi >= 4) {

        return 80;

    }

    else if (ghi >= 3) {

        return 70;

    }

    else if (ghi >= 2) {

        return 50;

    }

    else {

        return 30;

    }

}


// =========================================================
// WIND SCORE
// =========================================================

function calculateWindScore(wind) {

    if (wind >= 8) {

        return 100;

    }

    else if (wind >= 7) {

        return 90;

    }

    else if (wind >= 6) {

        return 80;

    }

    else if (wind >= 5) {

        return 70;

    }

    else if (wind >= 4) {

        return 60;

    }

    else if (wind >= 3) {

        return 50;

    }

    else {

        return 30;

    }

}


// =========================================================
// LAND SCORE
// =========================================================

function calculateLandScore(site) {

    if (!site) {

        return 50;

    }

    let score = 50;


    // Land type

    if (
        site.land_type &&
        site.land_type
            .toLowerCase()
            .includes("open")
    ) {

        score += 25;

    }


    // Land area

    const area =
        Number(
            site.land_area
        );


    if (area >= 20) {

        score += 25;

    }

    else if (area >= 10) {

        score += 15;

    }

    else if (area >= 5) {

        score += 10;

    }


    return Math.min(
        score,
        100
    );

}


// =========================================================
// LOAD SITE LOCATION
// =========================================================

async function loadSiteLocation(siteId) {

    try {

        const url =
            `http://127.0.0.1:8000/sites/${siteId}`;


        console.log(
            "Site URL:",
            url
        );


        const response =
            await fetch(url);


        console.log(
            "Site HTTP status:",
            response.status
        );


        const data =
            await response.json();


        console.log(
            "Site response:",
            data
        );


        if (!response.ok) {

            console.log(
                "Site API failed."
            );

            return null;

        }


        if (
            data.status !== "success"
        ) {

            console.log(
                "Site API returned error."
            );

            return null;

        }


        // =================================================
        // IMPORTANT
        // YOUR API RETURNS data.site
        // =================================================

        const site =
            data.site;


        if (!site) {

            console.log(
                "No site found."
            );

            return null;

        }


        console.log(
            "Selected site:",
            site
        );


        // =================================================
        // SITE DETAILS
        // =================================================

        const siteNameElement =
            document.getElementById(
                "siteName"
            );

        if (siteNameElement) {

            siteNameElement.innerText =
                site.site_name || "--";

        }


        const regionElement =
            document.getElementById(
                "region"
            );

        if (regionElement) {

            regionElement.innerText =
                site.region || "--";

        }


        const landAreaElement =
            document.getElementById(
                "landArea"
            );

        if (landAreaElement) {

            landAreaElement.innerText =
                site.land_area ?? "--";

        }


        const elevationElement =
            document.getElementById(
                "elevation"
            );

        if (elevationElement) {

            elevationElement.innerText =
                site.elevation ?? "--";

        }


        const landTypeElement =
            document.getElementById(
                "landType"
            );

        if (landTypeElement) {

            landTypeElement.innerText =
                site.land_type || "--";

        }


        const ownershipElement =
            document.getElementById(
                "ownership"
            );

        if (ownershipElement) {

            ownershipElement.innerText =
                site.ownership || "--";

        }


        // =================================================
        // COORDINATES
        // =================================================

        const latitude =
            Number(
                site.latitude
            );

        const longitude =
            Number(
                site.longitude
            );


        if (
            !Number.isFinite(latitude) ||
            !Number.isFinite(longitude)
        ) {

            console.log(
                "Invalid coordinates."
            );

            return site;

        }


        const latitudeElement =
            document.getElementById(
                "latitude"
            );

        if (latitudeElement) {

            latitudeElement.innerText =
                latitude.toFixed(5);

        }


        const longitudeElement =
            document.getElementById(
                "longitude"
            );

        if (longitudeElement) {

            longitudeElement.innerText =
                longitude.toFixed(5);

        }


        console.log(
            "Latitude:",
            latitude
        );

        console.log(
            "Longitude:",
            longitude
        );


        // =================================================
        // CREATE MAP
        // =================================================

        createMap(
            latitude,
            longitude,
            site.site_name,
            site.region
        );


        return site;

    }

    catch (error) {

        console.error(
            "Location error:",
            error
        );

        return null;

    }

}


// =========================================================
// CREATE MAP
// =========================================================

function createMap(
    latitude,
    longitude,
    siteName,
    region
) {

    // Remove old map

    if (map !== null) {

        map.remove();

        map = null;

    }


    // Create map

    map =
        L.map("map")
            .setView(
                [
                    latitude,
                    longitude
                ],
                12
            );


    // OpenStreetMap

    L.tileLayer(

        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",

        {

            maxZoom: 19,

            attribution:
                "&copy; OpenStreetMap contributors"

        }

    ).addTo(map);


    // Marker

    marker =
        L.marker(
            [
                latitude,
                longitude
            ]
        )
            .addTo(map);


    // Popup

    marker
        .bindPopup(

            `<b>☀️ ${siteName || "Site"}</b><br>
             📍 ${region || "Unknown region"}<br>
             🌱 Renewable Energy Site`

        )
        .openPopup();

}


// =========================================================
// CURRENT SOLAR CHART
// =========================================================

function createSolarChart(
    ghi,
    dni,
    dhi,
    predictedGhi
) {

    const canvas =
        document.getElementById(
            "solarChart"
        );


    if (!canvas) {

        console.error(
            "solarChart canvas not found"
        );

        return;

    }


    if (solarChart !== null) {

        solarChart.destroy();

    }


    solarChart =
        new Chart(

            canvas,

            {

                type: "bar",


                data: {

                    labels: [

                        "GHI",

                        "DNI",

                        "DHI",

                        "Predicted GHI"

                    ],


                    datasets: [

                        {

                            label:
                                "Solar Radiation",

                            data: [

                                ghi,

                                dni,

                                dhi,

                                predictedGhi

                            ],


                            backgroundColor: [

                                "#f59e0b",

                                "#f97316",

                                "#facc15",

                                "#16a34a"

                            ],


                            borderRadius: 8

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,


                    plugins: {

                        legend: {

                            display: true

                        }

                    },


                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }

        );

}


// =========================================================
// CURRENT WIND CHART
// =========================================================

function createWindChart(
    currentWind,
    predictedWind
) {

    const canvas =
        document.getElementById(
            "windChart"
        );


    if (!canvas) {

        console.error(
            "windChart canvas not found"
        );

        return;

    }


    if (windChart !== null) {

        windChart.destroy();

    }


    windChart =
        new Chart(

            canvas,

            {

                type: "bar",


                data: {

                    labels: [

                        "Current Wind",

                        "Predicted Wind"

                    ],


                    datasets: [

                        {

                            label:
                                "Wind Speed",

                            data: [

                                currentWind,

                                predictedWind

                            ],


                            backgroundColor: [

                                "#0284c7",

                                "#06b6d4"

                            ],


                            borderRadius: 8

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,


                    plugins: {

                        legend: {

                            display: true

                        }

                    },


                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }

        );

}


// =========================================================
// LOAD HISTORICAL DATA
// =========================================================

async function loadHistoricalData(siteId) {

    try {

        console.log(
            "Loading historical data..."
        );


        const url =
            `http://127.0.0.1:8000/sites/${siteId}/historical-data`;


        console.log(
            "Historical URL:",
            url
        );


        const response =
            await fetch(url);


        console.log(
            "Historical HTTP status:",
            response.status
        );


        const result =
            await response.json();


        console.log(
            "Historical response:",
            result
        );


        if (!response.ok) {

            console.error(
                "Historical API failed."
            );

            return;

        }


        if (
            result.status !== "success"
        ) {

            console.error(
                result.message ||
                "Historical data unavailable."
            );

            return;

        }


        const records =
            result.data || [];


        if (records.length === 0) {

            console.log(
                "No historical records."
            );

            return;

        }


        console.log(
            "Historical records:",
            records.length
        );


        // =================================================
        // PREPARE DATA
        // =================================================

        const dates =
            records.map(
                row =>
                    row.recorded_date
            );


        const ghi =
            records.map(
                row =>
                    Number(row.ghi)
            );


        const dni =
            records.map(
                row =>
                    Number(row.dni)
            );


        const dhi =
            records.map(
                row =>
                    Number(row.dhi)
            );


        const wind =
            records.map(
                row =>
                    Number(row.wind_speed)
            );


        // =================================================
        // CALCULATE AVERAGES
        // =================================================

        const averageGhi =
            ghi.reduce(
                (sum, value) =>
                    sum + value,
                0
            ) / ghi.length;


        const averageWind =
            wind.reduce(
                (sum, value) =>
                    sum + value,
                0
            ) / wind.length;


        // =================================================
        // MAXIMUM VALUES
        // =================================================

        const maximumGhi =
            Math.max(...ghi);


        const maximumWind =
            Math.max(...wind);


        // =================================================
        // DISPLAY SUMMARY
        // =================================================

        const averageGhiElement =
            document.getElementById(
                "averageGhi"
            );

        if (averageGhiElement) {

            averageGhiElement.innerText =
                averageGhi.toFixed(2);

        }


        const averageWindElement =
            document.getElementById(
                "averageWind"
            );

        if (averageWindElement) {

            averageWindElement.innerText =
                averageWind.toFixed(2);

        }


        const maximumGhiElement =
            document.getElementById(
                "maximumGhi"
            );

        if (maximumGhiElement) {

            maximumGhiElement.innerText =
                maximumGhi.toFixed(2);

        }


        const maximumWindElement =
            document.getElementById(
                "maximumWind"
            );

        if (maximumWindElement) {

            maximumWindElement.innerText =
                maximumWind.toFixed(2);

        }


        // =================================================
        // DATE RANGE
        // =================================================

        const startDateElement =
            document.getElementById(
                "historicalStartDate"
            );

        if (startDateElement) {

            startDateElement.innerText =
                dates[0];

        }


        const endDateElement =
            document.getElementById(
                "historicalEndDate"
            );

        if (endDateElement) {

            endDateElement.innerText =
                dates[dates.length - 1];

        }


        // =================================================
        // CREATE HISTORICAL SOLAR CHART
        // =================================================

        createHistoricalSolarChart(
            dates,
            ghi,
            dni,
            dhi
        );


        // =================================================
        // CREATE HISTORICAL WIND CHART
        // =================================================

        createHistoricalWindChart(
            dates,
            wind
        );

    }

    catch (error) {

        console.error(
            "Historical data error:",
            error
        );

    }

}


// =========================================================
// HISTORICAL SOLAR CHART
// =========================================================

function createHistoricalSolarChart(
    dates,
    ghi,
    dni,
    dhi
) {

    const canvas =
        document.getElementById(
            "historicalSolarChart"
        );


    if (!canvas) {

        console.error(
            "historicalSolarChart canvas not found."
        );

        return;

    }


    if (
        historicalSolarChart !== null
    ) {

        historicalSolarChart.destroy();

    }


    historicalSolarChart =
        new Chart(

            canvas,

            {

                type: "line",


                data: {

                    labels: dates,


                    datasets: [

                        {

                            label:
                                "GHI",

                            data:
                                ghi,

                            borderWidth:
                                2,

                            tension:
                                0.3,

                            pointRadius:
                                0

                        },


                        {

                            label:
                                "DNI",

                            data:
                                dni,

                            borderWidth:
                                2,

                            tension:
                                0.3,

                            pointRadius:
                                0

                        },


                        {

                            label:
                                "DHI",

                            data:
                                dhi,

                            borderWidth:
                                2,

                            tension:
                                0.3,

                            pointRadius:
                                0

                        }

                    ]

                },


                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        false,


                    interaction: {

                        mode:
                            "index",

                        intersect:
                            false

                    },


                    plugins: {

                        legend: {

                            display:
                                true

                        }

                    },


                    scales: {

                        x: {

                            ticks: {

                                maxTicksLimit:
                                    12

                            }

                        },


                        y: {

                            beginAtZero:
                                true,

                            title: {

                                display:
                                    true,

                                text:
                                    "Solar Radiation"

                            }

                        }

                    }

                }

            }

        );

}


// =========================================================
// HISTORICAL WIND CHART
// =========================================================

function createHistoricalWindChart(
    dates,
    wind
) {

    const canvas =
        document.getElementById(
            "historicalWindChart"
        );


    if (!canvas) {

        console.error(
            "historicalWindChart canvas not found."
        );

        return;

    }


    if (
        historicalWindChart !== null
    ) {

        historicalWindChart.destroy();

    }


    historicalWindChart =
        new Chart(

            canvas,

            {

                type: "line",


                data: {

                    labels:
                        dates,


                    datasets: [

                        {

                            label:
                                "Wind Speed",

                            data:
                                wind,

                            borderWidth:
                                2,

                            tension:
                                0.3,

                            pointRadius:
                                0

                        }

                    ]

                },


                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        false,


                    interaction: {

                        mode:
                            "index",

                        intersect:
                            false

                    },


                    plugins: {

                        legend: {

                            display:
                                true

                        }

                    },


                    scales: {

                        x: {

                            ticks: {

                                maxTicksLimit:
                                    12

                            }

                        },


                        y: {

                            beginAtZero:
                                true,

                            title: {

                                display:
                                    true,

                                text:
                                    "Wind Speed (m/s)"

                            }

                        }

                    }

                }

            }

        );

}
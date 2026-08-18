const NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search";

function getRegion(address) {
  return (
    address?.state ||
    address?.region ||
    address?.county ||
    address?.city ||
    address?.town ||
    address?.village ||
    ""
  );
}

export async function searchPlaces(query) {
  const normalizedQuery = query.trim();

  if (normalizedQuery.length < 2) {
    return [];
  }

  const params = new URLSearchParams({
    q: normalizedQuery,
    format: "jsonv2",
    addressdetails: "1",
    limit: "5",
  });

  const response = await fetch(`${NOMINATIM_SEARCH_URL}?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Location search is unavailable. Enter coordinates manually.");
  }

  const results = await response.json();

  return results.map((result) => ({
    id: `${result.osm_type}-${result.osm_id}`,
    label: result.display_name,
    latitude: Number(result.lat),
    longitude: Number(result.lon),
    region: getRegion(result.address),
  }));
}

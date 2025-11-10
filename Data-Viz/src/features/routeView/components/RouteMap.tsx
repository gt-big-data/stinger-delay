import React from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Marker,
  Popup,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Stop } from "@/types/stop";
import { Route } from "@/types/route";
import { LiveBusLocation } from "@/types/delay";
import bus_icon_url from "../../../assets/Bus.png";

// Custom icon for buses
const busIcon = L.icon({
  iconUrl: bus_icon_url,
  iconRetinaUrl: bus_icon_url,
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -30],
});

interface RouteMapProps {
  stops: Stop[];
  routes: Route[];
  busLocations?: LiveBusLocation[];
  pathCoordinates?: [number, number][];
}

const RouteMap: React.FC<RouteMapProps> = ({
  stops,
  routes,
  busLocations = [],
  pathCoordinates,
}) => {
  const center: [number, number] = stops.length
    ? [stops[0].latitude, stops[0].longitude]
    : [33.7756, -84.3963];

  const stopColor = (stopId: string): string => {
    const route = routes.find((r) => r.stops.some((s) => s.id === stopId));
    return route?.color || "#3388ff";
  };

  return (
    <MapContainer
      center={center}
      zoom={15}
      style={{ height: "100%", width: "100%" }}
      scrollWheelZoom={true}
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {pathCoordinates && (
        <Polyline positions={pathCoordinates} color="#b3a369" />
      )}

      {stops.map((stop) => (
        <CircleMarker
          key={stop.id}
          center={[stop.latitude, stop.longitude]}
          radius={10}
          fillColor="#fff"
          color={stopColor(stop.id)}
          fillOpacity={1}
          stroke={true}
          weight={3}
        >
          <Popup>{stop.name}</Popup>
        </CircleMarker>
      ))}

      {busLocations.map((bus) => (
        <Marker
          key={bus.busId}
          position={[bus.latitude, bus.longitude]}
          icon={busIcon}
        >
          <Popup>
            Bus {bus.busId} on Route {bus.routeId}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default RouteMap;

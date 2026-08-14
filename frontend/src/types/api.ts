export type UserRole = "ORGANIZER" | "CUSTOMER" | "GATE";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export type EventStatus = "DRAFT" | "PUBLISHED" | "CANCELLED";

export interface Event {
  id: string;
  organizer_id: string;
  external_provider: string;
  external_id: string;
  title: string;
  description: string | null;
  image_url: string | null;
  venue_name: string;
  venue_address: string;
  event_date: string;
  capacity: number;
  available_tickets: number;
  ticket_price: string;
  status: EventStatus;
  created_at: string;
  updated_at: string;
}

export interface CatalogEvent {
  external_id: string;
  title: string;
  description: string | null;
  image_url: string | null;
  venue_name: string;
  venue_address: string;
  event_date: string;
}


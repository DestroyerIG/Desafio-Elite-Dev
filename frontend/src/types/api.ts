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

export type ReservationStatus = "PENDING" | "PAID" | "CANCELLED" | "EXPIRED";

export interface Reservation {
  id: string;
  customer_id: string;
  event_id: string;
  quantity: number;
  unit_price: string;
  total_amount: string;
  status: ReservationStatus;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReservationEvent {
  id: string;
  title: string;
  image_url: string | null;
  venue_name: string;
  venue_address: string;
  event_date: string;
}

export interface CustomerReservation extends Reservation {
  event: ReservationEvent;
}

export type PaymentStatus = "APPROVED" | "DECLINED";

export interface Payment {
  id: string;
  reservation_id: string;
  amount: string;
  status: PaymentStatus;
  provider: string;
  failure_reason: string | null;
  tickets_created: number;
  ticket_ids: string[];
  created_at: string;
  updated_at: string;
}

export type TicketStatus = "ACTIVE" | "USED" | "CANCELLED";

export interface TicketEvent {
  id: string;
  title: string;
  image_url: string | null;
  venue_name: string;
  venue_address: string;
  event_date: string;
}

export interface Ticket {
  id: string;
  reservation_id: string;
  event_id: string;
  public_code: string;
  status: TicketStatus;
  used_at: string | null;
  created_at: string;
  event: TicketEvent;
}

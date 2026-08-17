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
export type SeatingMode = "GENERAL_ADMISSION" | "ASSIGNED";

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
  seating_mode: SeatingMode;
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

export type ReservationStatus =
  | "PENDING"
  | "PAID"
  | "REFUNDED"
  | "CANCELLED"
  | "EXPIRED";

export type SeatStatus = "AVAILABLE" | "HELD" | "SOLD";

export interface SeatSectionReference {
  id: string;
  name: string;
}

export interface ReservationSeat {
  id: string;
  row_label: string;
  number: number;
  label: string;
  section: SeatSectionReference;
}

export interface Seat extends Omit<ReservationSeat, "section"> {
  position: number;
  status: SeatStatus;
}

export interface SeatSection extends SeatSectionReference {
  position: number;
  row_count: number;
  seats_per_row: number;
  seats: Seat[];
}

export interface SeatMap {
  id: string;
  event_id: string;
  stage_label: string;
  version: number;
  sections: SeatSection[];
}

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
  seats: ReservationSeat[];
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

export type RefundStatus = "PENDING" | "APPROVED" | "FAILED";

export interface Refund {
  id: string;
  reservation_id: string;
  payment_id: string;
  amount: string;
  status: RefundStatus;
  provider: string;
  failure_reason: string | null;
  processed_at: string | null;
  tickets_refunded: number;
  reservation: Reservation;
  created_at: string;
  updated_at: string;
}

export type TicketStatus = "ACTIVE" | "USED" | "REFUNDED" | "CANCELLED";

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
  seat?: ReservationSeat;
}

export interface TicketShare {
  token: string;
  expires_at: string | null;
  created_at: string;
}

export interface SharedTicket {
  public_code: string;
  status: TicketStatus;
  used_at: string | null;
  event: TicketEvent;
  seat?: ReservationSeat;
}

export type ValidationResult =
  | "VALID"
  | "INVALID"
  | "ALREADY_USED"
  | "WRONG_EVENT";

export interface GateValidation {
  result: ValidationResult;
  message: string;
  ticket_id: string | null;
  public_code: string | null;
  validated_at: string;
}

-- HSK Việt 10 Slot – Supabase schema
-- Chạy toàn bộ trong Supabase SQL Editor.

create table if not exists public.hsk_slots (
  user_id uuid not null references auth.users(id) on delete cascade,
  slot_id smallint not null check (slot_id between 1 and 10),
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, slot_id)
);

alter table public.hsk_slots enable row level security;

revoke all on table public.hsk_slots from anon;
grant select, insert, update, delete on table public.hsk_slots to authenticated;

drop policy if exists "hsk_slots_select_own" on public.hsk_slots;
create policy "hsk_slots_select_own"
on public.hsk_slots for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "hsk_slots_insert_own" on public.hsk_slots;
create policy "hsk_slots_insert_own"
on public.hsk_slots for insert
to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "hsk_slots_update_own" on public.hsk_slots;
create policy "hsk_slots_update_own"
on public.hsk_slots for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists "hsk_slots_delete_own" on public.hsk_slots;
create policy "hsk_slots_delete_own"
on public.hsk_slots for delete
to authenticated
using ((select auth.uid()) = user_id);

create index if not exists hsk_slots_updated_at_idx on public.hsk_slots(updated_at desc);

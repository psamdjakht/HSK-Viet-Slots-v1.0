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

-- =============================================================
-- HỌC LIỆU HSK 1 DÙNG CHUNG + QUẢN TRỊ BẰNG MẬT KHẨU
-- Mật khẩu mặc định được chèn dưới dạng bcrypt, không lưu chữ rõ.
-- Sau khi chạy SQL, nên đổi mật khẩu ngay trong giao diện Quản trị.
-- =============================================================
create extension if not exists pgcrypto;

create table if not exists public.hsk_content_overrides (
  word_id text primary key,
  patch jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  updated_by uuid null references auth.users(id) on delete set null
);

alter table public.hsk_content_overrides enable row level security;
revoke all on table public.hsk_content_overrides from anon;
grant select on table public.hsk_content_overrides to authenticated;

drop policy if exists "hsk_content_read_all" on public.hsk_content_overrides;
create policy "hsk_content_read_all"
on public.hsk_content_overrides for select
to authenticated
using (true);

create table if not exists public.hsk_admin_config (
  config_key text primary key,
  password_hash text not null,
  updated_at timestamptz not null default now()
);

revoke all on table public.hsk_admin_config from anon, authenticated;

insert into public.hsk_admin_config(config_key, password_hash)
values ('main', '$2a$12$hV1u42eSDCvPP3IELpO6/.WhOveLV3Wku6gSACkKyL2aqncpwjtLW')
on conflict (config_key) do nothing;

create or replace function public.admin_verify_hsk_password(p_password text)
returns boolean
language plpgsql
security definer
set search_path = public, extensions
as $$
declare v_hash text;
begin
  select password_hash into v_hash from public.hsk_admin_config where config_key='main';
  return v_hash is not null and crypt(coalesce(p_password,''), v_hash) = v_hash;
end;
$$;

create or replace function public.admin_save_hsk_content(p_password text, p_word_id text, p_patch jsonb)
returns boolean
language plpgsql
security definer
set search_path = public, extensions
as $$
begin
  if not public.admin_verify_hsk_password(p_password) then
    raise exception 'Mật khẩu quản trị không đúng' using errcode='42501';
  end if;
  if p_word_id !~ '^L1-[0-9]{4}$' then
    raise exception 'Chỉ cho phép sửa ID từ HSK 1 hợp lệ';
  end if;
  if jsonb_typeof(p_patch) <> 'object' then
    raise exception 'Dữ liệu chỉnh sửa phải là JSON object';
  end if;
  insert into public.hsk_content_overrides(word_id,patch,updated_at,updated_by)
  values (p_word_id,p_patch,now(),auth.uid())
  on conflict(word_id) do update set patch=excluded.patch,updated_at=excluded.updated_at,updated_by=excluded.updated_by;
  return true;
end;
$$;

create or replace function public.admin_delete_hsk_content(p_password text, p_word_id text)
returns boolean
language plpgsql
security definer
set search_path = public, extensions
as $$
begin
  if not public.admin_verify_hsk_password(p_password) then
    raise exception 'Mật khẩu quản trị không đúng' using errcode='42501';
  end if;
  delete from public.hsk_content_overrides where word_id=p_word_id;
  return true;
end;
$$;

create or replace function public.admin_change_hsk_password(p_current_password text, p_new_password text)
returns boolean
language plpgsql
security definer
set search_path = public, extensions
as $$
begin
  if not public.admin_verify_hsk_password(p_current_password) then
    raise exception 'Mật khẩu quản trị hiện tại không đúng' using errcode='42501';
  end if;
  if length(coalesce(p_new_password,'')) < 8 then
    raise exception 'Mật khẩu mới phải có ít nhất 8 ký tự';
  end if;
  update public.hsk_admin_config
  set password_hash=crypt(p_new_password,gen_salt('bf',12)),updated_at=now()
  where config_key='main';
  return true;
end;
$$;

revoke all on function public.admin_verify_hsk_password(text) from public;
revoke all on function public.admin_save_hsk_content(text,text,jsonb) from public;
revoke all on function public.admin_delete_hsk_content(text,text) from public;
revoke all on function public.admin_change_hsk_password(text,text) from public;
grant execute on function public.admin_verify_hsk_password(text) to authenticated;
grant execute on function public.admin_save_hsk_content(text,text,jsonb) to authenticated;
grant execute on function public.admin_delete_hsk_content(text,text) to authenticated;
grant execute on function public.admin_change_hsk_password(text,text) to authenticated;

create index if not exists hsk_content_overrides_updated_idx on public.hsk_content_overrides(updated_at desc);

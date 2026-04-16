-- Supabase Metrics Setup (EU project önerilir)

create table if not exists public.events (
    id              bigserial primary key,
    received_at     timestamptz not null default now(),
    plugin_version  text,
    qgis_version    text,
    anon_user_id    uuid,
    event_date      date,
    event_hour      smallint,
    query_type      text not null,
    status          text,
    city            text,
    district        text,
    neighborhood    text,
    count           integer default 1,
    extra           jsonb
);

create index if not exists events_received_at_idx on public.events (received_at desc);
create index if not exists events_query_type_idx on public.events (query_type);
create index if not exists events_city_idx on public.events (city);
create index if not exists events_anon_user_idx on public.events (anon_user_id);

alter table public.events enable row level security;

drop policy if exists "anon can insert events" on public.events;
create policy "anon can insert events"
    on public.events
    for insert
    to anon
    with check (true);

create or replace function public.validate_event()
returns trigger
language plpgsql
as $$
begin
    if new.query_type not in (
        'plugin_start',
        'il_loaded',
        'ilce_loaded',
        'mahalle_loaded',
        'manual_query',
        'map_click_query',
        'building_bb_query'
    ) then
        raise exception 'invalid query_type: %', new.query_type;
    end if;

    if new.event_hour is not null and (new.event_hour < 0 or new.event_hour > 23) then
        raise exception 'invalid hour';
    end if;

    if new.count is null or new.count < 1 or new.count > 1000 then
        new.count := 1;
    end if;

    new.received_at := now();
    return new;
end;
$$;

drop trigger if exists validate_event_trigger on public.events;
create trigger validate_event_trigger
    before insert on public.events
    for each row execute function public.validate_event();

create or replace function public.rate_limit_events()
returns trigger
language plpgsql
as $$
declare
    recent_count int;
begin
    if new.anon_user_id is null then
        return new;
    end if;

    select count(*) into recent_count
    from public.events
    where anon_user_id = new.anon_user_id
      and received_at > now() - interval '1 minute';

    if recent_count > 100 then
        raise exception 'rate limit exceeded';
    end if;

    return new;
end;
$$;

drop trigger if exists rate_limit_trigger on public.events;
create trigger rate_limit_trigger
    before insert on public.events
    for each row
    when (new.anon_user_id is not null)
    execute function public.rate_limit_events();

create or replace view public.events_daily as
select
    event_date,
    query_type,
    status,
    city,
    count(*) as event_count,
    count(distinct anon_user_id) as unique_users
from public.events
where event_date is not null
group by event_date, query_type, status, city
order by event_date desc;

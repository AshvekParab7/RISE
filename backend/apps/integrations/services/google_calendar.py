from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .google_tokens import credentials_for

class CalendarApiError(Exception):
    def __init__(self, status, message): self.status = status; super().__init__(message)
class CalendarSyncTokenExpired(CalendarApiError): pass

class GoogleCalendarService:
    def __init__(self, connection, client_builder=build):
        self.client = client_builder('calendar', 'v3', credentials=credentials_for(connection), cache_discovery=False)

    def _collect(self, factory, key):
        items = []; token = None; next_sync = ''
        while True:
            try: payload = factory(token).execute()
            except HttpError as exc:
                status = getattr(exc.resp, 'status', 500)
                if status == 410: raise CalendarSyncTokenExpired(410, 'Calendar sync token expired.') from exc
                raise CalendarApiError(status, 'Google Calendar request failed.') from exc
            items.extend(payload.get(key, [])); next_sync = payload.get('nextSyncToken', next_sync); token = payload.get('nextPageToken')
            if not token: return items, next_sync

    def get_calendar_list(self, sync_token=None):
        return self._collect(lambda token: self.client.calendarList().list(maxResults=250, showDeleted=True, **({'syncToken': sync_token} if sync_token else {}), **({'pageToken': token} if token else {})), 'items')

    def get_event(self, calendar_id, event_id):
        try: return self.client.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except HttpError as exc: raise CalendarApiError(getattr(exc.resp, 'status', 500), 'Google Calendar event could not be loaded.') from exc

    def get_events(self, calendar_id, time_min, time_max, sync_token=None):
        params = {'calendarId': calendar_id, 'maxResults': 2500, 'singleEvents': False, 'showDeleted': True, 'orderBy': 'updated'}
        if sync_token: params['syncToken'] = sync_token
        else: params.update({'timeMin': time_min.isoformat(), 'timeMax': time_max.isoformat()})
        return self._collect(lambda token: self.client.events().list(**params, **({'pageToken': token} if token else {})), 'items')

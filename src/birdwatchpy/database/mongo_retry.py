import sys
import time

from pymongo.errors import AutoReconnect, PyMongoError

def print_warning(msg):
  """
  Prints a warning message to the terminal.
  """
  sys.stdout.write('%-15s%s\n' % ('WARN:', msg))


def mongo_retry(func, max_retry=20, delay_secs=2):
  """
  Retry decorator for mongodb operations.
  This decorator function allows for retry attempts against a given database
  operation. The purpose is cover situations where the replica set is in a
  state of transition. In the event that an operation is performed against the
  db while the replica set is re-electing a new primary, this function will
  sleep and retry.
  Args:
    max_retry: Maximum number of times to retry a database operation.
    delay_secs: Seconds to wait in between retry attempts.
  """
  def db_op_wrapper(*args, **kwargs):
    count = 0
    while count < max_retry:
      try:
        return func(*args, **kwargs)
      except AutoReconnect as e:
        print(e)
        print_warning('Op failed to complete...retrying')
        count += 1
        time.sleep(delay_secs)
      except PyMongoError as err:
        print(err)
        return False, str(err)
    return False, str('Op failed after too many retries')
  return db_op_wrapper
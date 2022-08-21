package ops

import (
	L "Goat/analysis/lattice"
)

func Lock(val L.AbstractValue) L.OpOutcomes {
	// Constants
	LOCKED, UNLOCKED := L.Consts().Mutex()
	BLOCKS, SUCCEED, _ := L.Consts().OpOutcomes()

	switch {
	case val.IsMutex():
		mu := val.MutexValue()

		if mu.Geq(UNLOCKED) {
			// If the lock may be unlocked, the only outcome is a successful lock.
			return SUCCEED(val.UpdateMutex(LOCKED))
		}
	case val.IsRWMutex():
		NORLOCKS := L.Elements().FlatInt(0)

		mu := val.RWMutexValue()

		if mu.Status().Geq(UNLOCKED) &&
			mu.RLocks().Geq(NORLOCKS) {
			// If the write lock may be unlocked, and there may be no read locks, there is a
			// successful outcome where the lock is now locked, and there are guaranteed
			// no read locks.
			return SUCCEED(val.UpdateRWMutex(
				mu.UpdateStatus(LOCKED).UpdateRLocks(NORLOCKS)))
		}
	}

	// If the lock is at most locked, the only outcome is blocking.
	return BLOCKS
}

func Unlock(val L.AbstractValue) L.OpOutcomes {
	// Constants
	LOCKED, UNLOCKED := L.Consts().Mutex()
	BLOCKS, SUCCEED, PANICS := L.Consts().OpOutcomes()

	OUTCOME := BLOCKS

	switch {
	case val.IsMutex():
		mu := val.MutexValue()

		if mu.Geq(UNLOCKED) {
			// If the lock may be unlocked, the outcome may be a fatal exception.
			OUTCOME = OUTCOME.MonoJoin(PANICS(val.UpdateMutex(UNLOCKED)))
		}
		if mu.Geq(LOCKED) {
			// If the lock may be locked, the outcome may be a successful unlocking.
			OUTCOME = OUTCOME.MonoJoin(SUCCEED(val.UpdateMutex(UNLOCKED)))
		}
	case val.IsRWMutex():
		NORLOCKS := L.Elements().FlatInt(0)

		mu := val.RWMutex()

		if mu.Status().Geq(UNLOCKED) {
			// If the lock may be unlocked, the outcome may be a fatal exception
			OUTCOME = OUTCOME.MonoJoin(PANICS(val.UpdateRWMutex(
				mu.UpdateStatus(UNLOCKED))))
		}
		if mu.Status().Geq(LOCKED) {
			// If the lock may be locked, the outcome may be a successful locking where
			// it is guaranteed that no read locks are present.

			OUTCOME = OUTCOME.MonoJoin(SUCCEED(val.UpdateRWMutex(
				mu.UpdateStatus(UNLOCKED).UpdateRLocks(NORLOCKS))))
		}
	}

	return OUTCOME
}

func RLock(val L.AbstractValue) L.OpOutcomes {
	// Consts
	UNLOCKED := L.Consts().Unlocked()
	BLOCKS, SUCCEED, _ := L.Consts().OpOutcomes()

	mu := val.RWMutex()

	if mu.Status().Geq(UNLOCKED) {
		// Performing a read lock is only possible if the mutex may be unlocked.
		rlocks := mu.RLocks()

		switch {
		case rlocks.IsBot():
			panic("what?")
		case rlocks.IsTop():
			// If the amount of read locks is unknown, the outcome of read locking may
			// be a successful read lock, where the lock is guaranteed to not be
			// locked, but the amount of read locks is still unknown.
			return SUCCEED(val.UpdateRWMutex(
				mu.UpdateStatus(UNLOCKED),
			))
		default:
			// If the amount of read locks is known, then add 1 to it.
			// The successful outcome also states that the mutex is definitely not
			// fully locked.
			rls := rlocks.FlatInt().IValue()

			return SUCCEED(val.UpdateRWMutex(
				mu.UpdateRLocks(L.Elements().FlatInt(rls + 1)).UpdateStatus(UNLOCKED)))
		}
	}

	return BLOCKS
}

func RUnlock(val L.AbstractValue) L.OpOutcomes {
	// Consts
	LOCKED, UNLOCKED := L.Consts().Mutex()
	BLOCKS, SUCCEED, PANIC := L.Consts().OpOutcomes()

	OUTCOME := BLOCKS

	mu := val.RWMutex()

	if mu.Status().Geq(UNLOCKED) {
		// Success scenarios are only possible if the read mutex may be unlocked.
		rlocks := mu.RLocks()

		switch {
		case rlocks.IsBot():
			panic("what?")
		case rlocks.IsTop():
			// If the amount of read locks is unkown, then read unlocking may either
			// succeed, in which case the mutex is guaranteed to be write unlocked, but
			// the amount of read locks is still unknown, or may throw a fatal
			// exception, in which case the value is preserved.
			OUTCOME = OUTCOME.MonoJoin(SUCCEED(
				val.UpdateRWMutex(mu.UpdateStatus(UNLOCKED)),
			)).MonoJoin(PANIC(val))
		default:
			// If the amount of read locks is known, then the operation is guaranteed
			// to throw a fatal exception if no read locks are held, or to succeed by
			// decrementing the amount of read locks. In the latter scenario, the lock
			// is also guaranteed to be write unlocked.
			rls := rlocks.FlatInt().IValue()
			switch rls {
			case 0:
				OUTCOME = OUTCOME.MonoJoin(PANIC(val))
			default:
				OUTCOME = OUTCOME.MonoJoin(SUCCEED(
					val.UpdateRWMutex(mu.UpdateStatus(
						UNLOCKED,
					).UpdateRLocks(
						L.Elements().FlatInt(rls - 1)))))
			}
		}
	}
	if mu.Status().Geq(LOCKED) {
		// If the mutex may be write locked, then the assumption is that no read
		// locks were present at that point, meaning that read unlocking will throw
		// a fatal exception.
		OUTCOME = OUTCOME.MonoJoin(PANIC(val))
	}

	return OUTCOME
}

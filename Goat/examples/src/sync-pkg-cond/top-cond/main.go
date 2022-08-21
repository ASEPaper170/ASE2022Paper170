package main

import "sync"

func f(c *sync.Cond) {
	go func() {
		c.Signal()
	}()
	c.L.Lock()
	c.Wait()
	c.L.Unlock()
}

func main() {
	c1 := sync.NewCond(&sync.Mutex{})
	f(c1)
	f(sync.NewCond(&sync.RWMutex{}))
}

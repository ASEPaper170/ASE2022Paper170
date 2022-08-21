// Command squaring-fanin-bad comes from Golang blog to demonstrate fan-in and
// explicit cancellation. This version uses fan-in but not all values are
// consumed (resources leak).
//
// Source: https://blog.golang.org/pipelines
package main

// GoLive: replaced fmt.Println with println

import (
	//"fmt"
	"sync"
)

// The first stage, gen, is a function that converts a list of integers to a
// channel that emits the integers in the list. The gen function starts a
// goroutine that sends the integers on the channel and closes the channel when
// all the values have been sent:
func gen(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		for _, n := range nums {
			out <- n
		}
		close(out)
	}()
	return out
}

// The second stage, sq, receives integers from a channel and returns a channel
// that emits the square of each received integer. After the inbound channel is
// closed and this stage has sent all the values downstream, it closes the
// outbound channel:
func sq(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		for n := range in {
			out <- n * n
		}
		close(out)
	}()
	return out
}

func merge(cs ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	out := make(chan int)

	// Start an output goroutine for each input channel in cs.  output
	// copies values from c to out until c is closed, then calls wg.Done.
	output := func(c <-chan int) {
		for n := range c {
			out <- n
		}
		wg.Done()
	}
	wg.Add(len(cs))
	for _, c := range cs {
		go output(c)
	}

	// Start a goroutine to close out once all the output goroutines are
	// done.  This must start after the wg.Add call.
	go func() {
		wg.Wait()
		close(out)
	}()
	return out
}

func main() {
	in := gen(2, 3)

	// Distribute the sq work across two goroutines that both read from in.
	c1 := sq(in)
	c2 := sq(in)

	// Consume the first value from output
	out := merge(c1, c2)
	println(<-out)
	return
	// Since we didn't receive the second value from out,
	// one of the output goroutines is hung attempting to send it.
}

package defs

import (
	"Goat/utils"
	"fmt"
	"log"
	"sort"
	"strings"

	i "Goat/utils/indenter"

	"github.com/benbjohnson/immutable"
)

//go:generate go run generate-hasher.go Superloc Superlocation

type pathCondition struct{}

type Superloc struct {
	threads *immutable.Map
	pc      pathCondition
}

func (factory) Superloc(threads map[Goro]CtrLoc) Superloc {
	mp := immutable.NewMapBuilder(hashergoro{})
	for tid, loc := range threads {
		mp.Set(tid, loc)
	}
	return Superloc{
		mp.Map(),
		struct{}{},
	}
}

func (factory) EmptySuperloc() Superloc {
	return Create().Superloc(nil)
}

// Method for retrieving the main goroutine (identified as the root goroutine).
func (s Superloc) Main() Goro {
	for iter := s.threads.Iterator(); !iter.Done(); {
		k, _ := iter.Next()
		g := k.(Goro)
		if g.IsRoot() {
			return g
		}
	}
	panic(fmt.Sprintf("No main goroutine for superlocation %s", s))
}

func NewSuperlocationMap() *immutable.Map {
	return immutable.NewMap(hasherSuperloc{})
}

func (s Superloc) Size() int {
	return s.threads.Len()
}

func (s Superloc) Threads() *immutable.Map {
	return s.threads
}

func (s Superloc) GetUnsafe(g Goro) CtrLoc {
	cl, found := s.threads.Get(g)
	if !found {
		log.Fatal("Queried for inexistent thread", g, "in superlocation", s)
	}
	return cl.(CtrLoc)
}

func (s Superloc) Get(tid Goro) (CtrLoc, bool) {
	if cl, found := s.threads.Get(tid); found {
		return cl.(CtrLoc), true
	}
	return CtrLoc{}, false
}

func (s *Superloc) UpdateThread(tid Goro, loc CtrLoc) *Superloc {
	s.threads = s.threads.Set(tid, loc)
	return s
}

func (s *Superloc) UpdatePathCondition(pc pathCondition) *Superloc {
	s.pc = pc
	return s
}

func (s Superloc) Hash() uint32 {
	hashes := []uint32{}
	iter := s.Threads().Iterator()

	for !iter.Done() {
		ig, icl := iter.Next()
		g := ig.(Goro)
		cl := icl.(CtrLoc)
		hashes = append(hashes, utils.HashCombine(g.Hash(), cl.Hash()))
	}

	sort.Slice(hashes, func(i, j int) bool {
		return hashes[i] < hashes[j]
	})

	return utils.HashCombine(hashes...)
}

func (s Superloc) String() string {
	hashes := []func() string{}
	iter := s.Threads().Iterator()

	for !iter.Done() {
		ig, iloc := iter.Next()
		g := ig.(Goro)
		cl := iloc.(CtrLoc)
		hashes = append(hashes, func() string {
			var clstr string
			if cl.Panicked() {
				clstr = colorize.Panic(cl.String())
			} else {
				clstr = colorize.Superloc(cl.String())
			}
			return g.String() + " ⇒ " + clstr
		})
	}

	return i.Indenter().Start("⟨").NestThunkedPresep("| ", hashes...).End("⟩")
}

func (s Superloc) StringWithPos() string {
	hashes := []string{}
	iter := s.Threads().Iterator()

	for !iter.Done() {
		ig, iloc := iter.Next()
		g := ig.(Goro)
		cl := iloc.(CtrLoc)
		hashes = append(hashes, func() string {
			var clstr string
			if cl.Panicked() {
				clstr = colorize.Panic(cl.String())
			} else {
				clstr = colorize.Superloc(cl.String())
			}
			if pos := cl.PosString(); pos != "" {
				clstr += "\n" + pos
			}
			return g.String() + " ⇒ " + clstr
		}())
	}

	return "⟨ " + strings.Join(hashes, "\n| ")
}

func (s Superloc) ForEach(do func(Goro, CtrLoc)) {
	iter := s.threads.Iterator()
	for !iter.Done() {
		g, cl := iter.Next()
		do(g.(Goro), cl.(CtrLoc))
	}
}

func (s Superloc) Find(find func(Goro, CtrLoc) bool) (Goro, CtrLoc, bool) {
	iter := s.threads.Iterator()
	for !iter.Done() {
		k, v := iter.Next()
		g := k.(Goro)
		cl := v.(CtrLoc)
		if find(g, cl) {
			return g, cl, true
		}
	}

	return goro{}, CtrLoc{}, false
}

func (s Superloc) FindAll(find func(Goro, CtrLoc) bool) map[Goro]CtrLoc {
	res := make(map[Goro]CtrLoc)
	s.ForEach(func(g Goro, cl CtrLoc) {
		if find(g, cl) {
			res[g] = cl
		}
	})

	return res
}

func (s Superloc) Derive(threads map[Goro]CtrLoc) Superloc {
	for g, cl := range threads {
		s.threads = s.threads.Set(g, cl)
	}
	return s
}

func (s Superloc) DeriveThread(g Goro, cl CtrLoc) Superloc {
	s.threads = s.threads.Set(g, cl)
	return s
}

func (s1 Superloc) Equal(s2 Superloc) bool {
	if s1.Size() != s2.Size() {
		return false
	}

	_, _, res := s1.Find(func(g Goro, cl1 CtrLoc) bool {
		cl2, found := s2.Get(g)
		return !(found && cl1.Equal(cl2))
	})
	return !res
}

func (s Superloc) Root() Goro {
	g, _, _ := s.Find(func(g Goro, cl CtrLoc) bool {
		return true
	})

	return g.Root()
}

// Returns the next available index for goroutines.
func (s Superloc) NextIndex(g1 Goro) int {
	gs := s.FindAll(func(g2 Goro, cl CtrLoc) bool {
		return g1.WeakEqual(g2)
	})
	max := -1
	for g := range gs {
		i := g.Index()
		if i > max {
			max = i
		}
	}
	return max + 1
}

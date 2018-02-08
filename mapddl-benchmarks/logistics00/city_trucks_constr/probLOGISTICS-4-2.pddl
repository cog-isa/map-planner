(define (problem logistics-4-0-1) (:domain logistics)
(:objects
	obj21 - package
	obj22 - package
	obj11 - package
	obj12 - package
	pos1 - location
	pos2 - location
	apt1 - airport
	apt2 - airport
	cit1 - city
	cit2 - city
	tru1 - truck
	tru12 - truck
	tru2 - truck
	tru22 - truck
	heavy - weight
    light - weight
	)
(:init
	(at tru1 pos1)
	(at tru12 pos1)
	(at tru2 pos2)
	(at tru22 pos2)
	(at obj11 pos1)
	(at obj12 pos1)
	(at obj21 pos2)
	(at obj22 pos2)
	(in-city pos1 cit1)
	(in-city apt1 cit1)
	(in-city pos2 cit2)
	(in-city apt2 cit2)
	(empty tru1)
	(empty tru12)
	(empty tru2)
	(empty tru22)
	(cargo heavy obj21)
	(cargo light obj22)
	(cargo heavy obj11)
	(cargo light obj12)
)
(:goal
	(and
	    (at tru1 pos1)
	    (at tru12 pos1)
	    (at tru2 pos2)
	    (at tru22 pos2)
		(at obj11 apt1)
		(at obj22 apt2)
		(at obj12 apt1)
		(at obj21 apt2)
		(in-city pos1 cit1)
	    (in-city apt1 cit1)
	    (in-city pos2 cit2)
	    (in-city apt2 cit2)
        (empty tru1)
        (empty tru12)
        (empty tru2)
        (empty tru22)
        (cargo heavy obj21)
        (cargo light obj22)
        (cargo heavy obj11)
        (cargo light obj12)
	)
)

(:constraints
    (and
        (and (always (forall (?loc - location ?city - city ?truck - truck)
            (implies (in-city ?loc cit1) (at tru1 ?loc))))
        )
        (and (always (forall (?loc - location ?city - city ?truck - truck)
            (implies (in-city ?loc cit2) (at tru2 ?loc))))
        )
        (and (always (forall (?loc - location ?city - city ?truck - truck)
            (implies (in-city ?loc cit1) (at tru12 ?loc))))
        )
        (and (always (forall (?loc - location ?city - city ?truck - truck)
            (implies (in-city ?loc cit2) (at tru22 ?loc))))
        )
        (and (always (forall (?obj - package)
            (implies (cargo heavy ?obj) (in ?obj tru1))))
        )
        (and (always (forall (?obj - package)
            (implies (cargo heavy ?obj) (in ?obj tru2))))
        )
        (and (always (forall (?obj - package)
            (implies (cargo light ?obj) (in ?obj tru12))))
        )
        (and (always (forall (?obj - package)
            (implies (cargo light ?obj) (in ?obj tru22))))
        )
    )
)

)
(define (problem logistics-4-2) (:domain logistics)
(:objects
	apt1 - airport
	apt2 - airport
	apn1 - airplane
	obj11 - package
	obj13 - package
	obj12 - package
	pos1 - location
	tru1 - truck
	cit1 - city
	cit2 - city
	heavy - weight
	)
(:init
	(at tru1 pos1)
	(at apn1 apt1)
	(at obj11 pos1)
	(at obj12 pos1)
	(at obj13 pos1)
	(in-city pos1 cit1)
	(in-city apt1 cit1)
	(in-city apt2 cit2)
	(empty tru1)
	(empty apn1)
	(cargo heavy obj13)
	(cargo heavy obj11)
	(cargo heavy obj12)
)
(:goal
	(and
		(at tru1 pos1)
	    (at apn1 apt1)
	    (at obj11 apt2)
	    (at obj12 apt2)
	    (at obj13 apt2)
	    (in-city pos1 cit1)
	    (in-city apt1 cit1)
	    (in-city apt2 cit2)
	    (empty tru1)
	    (empty apn1)
	    (cargo heavy obj13)
	    (cargo heavy obj11)
	    (cargo heavy obj12)
	)
)

(:constraints
    (and
        (and (always (forall (?loc - location ?city - city ?truck - truck)
            (implies (in-city ?loc cit1) (at tru1 ?loc))))
        )
        (and (always (forall (?obj - package)
            (implies (cargo heavy ?obj) (in ?obj tru1))))
        )
    )
)

)
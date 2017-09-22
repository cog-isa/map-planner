(define (problem logistics-4-0-1) (:domain logistics)
(:objects
	apt1 - airport
	obj11 - package
	obj13 - package
	obj12 - package
	pos1 - location
	tru1 - truck
	cit1 - city
	)
(:init
	(at tru1 pos1)
	(at obj11 pos1)
	(at obj12 pos1)
	(at obj13 pos1)
	(in-city pos1 cit1)
	(in-city apt1 cit1)
	(empty tru1)
)
(:goal
	(and
		(at obj11 apt1)
		(at obj13 apt1)
		(at obj12 pos1)
		(in-city pos1 cit1)
	    (in-city apt1 cit1)
        (empty tru1)
	)
)

)
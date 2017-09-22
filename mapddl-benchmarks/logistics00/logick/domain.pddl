(define (domain logistics)
	(:requirements :typing :multi-agent)
(:types
	location vehicle package city - object
	airport - location
	truck - vehicle
)
(:predicates
	(at ?obj - object ?loc - location)
	(in ?obj - package ?veh - vehicle)
	(in-city ?loc - location ?city - city)
	(empty ?veh - vehicle)
)

(:action load-truck
	:agent (?truck - truck)
	:parameters (?obj - package ?loc - location ?veh - vehicle)
	:precondition (and
		(at ?truck ?loc)
		(at ?obj ?loc)
		(empty ?veh)
	)
	:effect (and
		(not (at ?obj ?loc))
		(not (empty ?veh))
		(in ?obj ?truck)
		(at ?truck ?loc)
	)
)


(:action unload-truck
	:agent (?truck - truck)
	:parameters (?obj - package ?loc - location ?veh - vehicle)
	:precondition (and
		(at ?truck ?loc)
		(in ?obj ?truck)
	)
	:effect (and
		(not (in ?obj ?truck))
		(at ?obj ?loc)
		(empty ?veh)
		(at ?truck ?loc)
	)
)


(:action drive-truck
	:agent (?truck - truck)
	:parameters (?loc-from - location ?loc-to - location ?city - city)
	:precondition (and
		(at ?truck ?loc-from)
	)
	:effect (and
		(not (at ?truck ?loc-from))
		(at ?truck ?loc-to)
	)
)

)
(define (domain logistics)
	(:requirements :typing :multi-agent)
(:types
	location vehicle package city weight - object
	airport - location
	truck airplane - vehicle
)
(:predicates
	(at ?obj - object ?loc - location)
	(in ?obj - package ?veh - vehicle)
	(in-city ?loc - location ?city - city)
	(empty ?veh - vehicle)
	(cargo ?w - weight ?obj - package)
)

(:action load-airplane
	:agent (?airplane - airplane)
	:parameters (?obj - package ?loc - airport ?veh - vehicle)
	:precondition (and
		(at ?obj ?loc)
		(at ?airplane ?loc)
		(empty ?veh)
	)
	:effect (and
		(not (at ?obj ?loc))
		(not (empty ?veh))
		(in ?obj ?airplane)
		(at ?airplane ?loc)
	)
)


(:action unload-airplane
	:agent (?airplane - airplane)
	:parameters (?obj - package ?loc - airport ?veh - vehicle)
	:precondition (and
		(in ?obj ?airplane)
		(at ?airplane ?loc)
	)
	:effect (and
		(not (in ?obj ?airplane))
		(at ?obj ?loc)
		(empty ?veh)
		(at ?airplane ?loc)
	)
)


(:action fly-airplane
	:agent (?airplane - airplane)
	:parameters (?loc-from - airport ?loc-to - airport)
	:precondition (and
		(at ?airplane ?loc-from)
	)
	:effect (and
		(not (at ?airplane ?loc-from))
		(at ?airplane ?loc-to)
	)
)


(:action load-truck
	:agent (?truck - truck)
	:parameters (?obj - package ?loc - location ?veh - vehicle ?w - weight)
	:precondition (and
		(at ?truck ?loc)
		(at ?obj ?loc)
		(cargo ?w ?obj)
		(empty ?veh)
	)
	:effect (and
		(not (at ?obj ?loc))
		(not (empty ?veh))
		(in ?obj ?truck)
		(at ?truck ?loc)
		(cargo ?w ?obj)
	)
)


(:action unload-truck
	:agent (?truck - truck)
	:parameters (?obj - package ?loc - location ?veh - vehicle ?w - weight)
	:precondition (and
		(at ?truck ?loc)
		(in ?obj ?truck)
		(cargo ?w ?obj)
	)
	:effect (and
		(not (in ?obj ?truck))
		(at ?obj ?loc)
		(empty ?veh)
		(at ?truck ?loc)
		(cargo ?w ?obj)
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
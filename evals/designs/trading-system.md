# Low-latency equities trading system

Team: 12 engineers. Colocated in one exchange data centre. Scale range to explain: a 3-person startup trading one venue up to a firm trading 8 venues.

Components:
- Market-data handlers that receive exchange feeds (about 2 million updates per second at peak across venues) and build order books.
- Strategy processes that read the books and decide to trade.
- Pre-trade risk checks (position limits, fat-finger price checks) before every order.
- Order gateway that sends orders to each venue and receives fills.
- Trade capture: every order and fill is stored for regulatory audit for 7 years.
- End-of-day P&L and reporting for the risk team.
- Monitoring dashboards for the trading desk.

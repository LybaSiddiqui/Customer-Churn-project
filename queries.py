SECTION_COLORS = {
    "Basic":        "#2563eb",
    "Intermediate": "#059669",
    "Advanced":     "#7c3aed",
}
SECTION_DESCRIPTIONS = {
    "Basic":        "Joins, filters, and ordering",
    "Intermediate": "GROUP BY, HAVING, and subqueries",
    "Advanced":     "Window functions, CTEs, triggers, procedures, views, and indexes",
}

# ── original 25 queries ───────────────────────────────────────
QUERIES = [
    {"id":1,"section":"Basic","title":"Full customer list with registration year",
     "purpose":"Get all customers showing full name, gender, and the year they registered.",
     "sql":"""SELECT customerid, firstname || ' ' || lastname AS fullname, gender, age,
    EXTRACT(YEAR FROM registrationdate) AS registrationyear
FROM customers ORDER BY registrationdate DESC LIMIT 100;"""},

    {"id":2,"section":"Basic","title":"Transactions with customer and product info",
     "purpose":"Show each transaction alongside the customer's name and the product they bought.",
     "sql":"""SELECT t.transactionid, c.firstname||' '||c.lastname AS customername,
    p.productname, p.category, t.quantity, t.totalamount, t.transactiondate
FROM transactions t
JOIN customers c ON t.customerid=c.customerid
JOIN products  p ON t.productid=p.productid
ORDER BY t.transactiondate DESC LIMIT 100;"""},

    {"id":3,"section":"Basic","title":"High Value customers with contact info",
     "purpose":"List only 'High Value' customers with their contact info and segment.",
     "sql":"""SELECT c.customerid, c.firstname||' '||c.lastname AS fullname,
    c.email, s.segmentlabel, s.clusterid
FROM customers c
JOIN segmentation_results s ON c.customerid=s.customerid
WHERE s.segmentlabel='High Value' ORDER BY c.customerid LIMIT 100;"""},

    {"id":4,"section":"Basic","title":"Product catalog sorted by price",
     "purpose":"Display all products from most to least expensive.",
     "sql":"SELECT productid, productname, category, price FROM products ORDER BY price DESC LIMIT 100;"},

    {"id":5,"section":"Basic","title":"Transactions within second half of 2025",
     "purpose":"Retrieve all transactions made in the second half of 2025.",
     "sql":"""SELECT t.transactionid, t.customerid, p.productname, t.totalamount, t.transactiondate
FROM transactions t JOIN products p ON t.productid=p.productid
WHERE t.transactiondate BETWEEN '2025-07-01' AND '2025-12-31'
ORDER BY t.transactiondate LIMIT 100;"""},

    {"id":6,"section":"Basic","title":"Active customers with behavioral stats",
     "purpose":"Show purchase behavior only for customers who have made at least one purchase.",
     "sql":"""SELECT c.customerid, c.firstname||' '||c.lastname AS fullname,
    bm.purchasefrequency, bm.averagespending, bm.recencyofpurchase
FROM customers c JOIN behavioral_metrics bm ON c.customerid=bm.customerid
WHERE bm.purchasefrequency>0 ORDER BY bm.averagespending DESC LIMIT 100;"""},

    {"id":7,"section":"Basic","title":"Male customers aged 30–50",
     "purpose":"Filter customers by gender and age range for targeted campaigns.",
     "sql":"""SELECT customerid, firstname||' '||lastname AS fullname, age, email, phone
FROM customers WHERE gender='Male' AND age BETWEEN 30 AND 50 ORDER BY age LIMIT 100;"""},

    {"id":8,"section":"Basic","title":"Electronics products under $300",
     "purpose":"Find affordable electronics for promotional listings.",
     "sql":"SELECT productid, productname, price FROM products WHERE category='Electronics' AND price<300 ORDER BY price LIMIT 100;"},

    {"id":9,"section":"Intermediate","title":"Revenue and order count per category",
     "purpose":"Summarize sales performance broken down by product category.",
     "sql":"""SELECT p.category, COUNT(t.transactionid) AS totalorders,
    SUM(t.totalamount) AS totalrevenue,
    ROUND(AVG(t.totalamount)::numeric,2) AS avgordervalue
FROM transactions t JOIN products p ON t.productid=p.productid
GROUP BY p.category ORDER BY totalrevenue DESC;"""},

    {"id":10,"section":"Intermediate","title":"Customers with more than 3 transactions",
     "purpose":"Identify frequent buyers who have placed more than 3 orders.",
     "sql":"""SELECT t.customerid, c.firstname||' '||c.lastname AS fullname,
    COUNT(t.transactionid) AS totaltransactions, SUM(t.totalamount) AS totalspent
FROM transactions t JOIN customers c ON t.customerid=c.customerid
GROUP BY t.customerid, c.firstname, c.lastname
HAVING COUNT(t.transactionid)>3 ORDER BY totaltransactions DESC LIMIT 100;"""},

    {"id":11,"section":"Intermediate","title":"Average spending per segment (HAVING > 600)",
     "purpose":"Compare spending averages across segments, showing only those above $600.",
     "sql":"""SELECT s.segmentlabel, COUNT(s.customerid) AS customercount,
    ROUND(AVG(bm.averagespending)::numeric,2) AS avgspending,
    ROUND(AVG(bm.purchasefrequency)::numeric,2) AS avgfrequency
FROM segmentation_results s JOIN behavioral_metrics bm ON s.customerid=bm.customerid
GROUP BY s.segmentlabel HAVING AVG(bm.averagespending)>600 ORDER BY avgspending DESC;"""},

    {"id":12,"section":"Intermediate","title":"Customers above overall average spending",
     "purpose":"Find customers whose average spending exceeds the database-wide average.",
     "sql":"""SELECT c.customerid, c.firstname||' '||c.lastname AS fullname, bm.averagespending
FROM customers c JOIN behavioral_metrics bm ON c.customerid=bm.customerid
WHERE bm.averagespending>(SELECT AVG(averagespending) FROM behavioral_metrics WHERE averagespending>0)
ORDER BY bm.averagespending DESC LIMIT 100;"""},

    {"id":13,"section":"Intermediate","title":"Top 5 best-selling products by quantity",
     "purpose":"Use a subquery to rank products and return only the top 5 sellers.",
     "sql":"""SELECT productname, category, totalsold FROM (
    SELECT p.productname, p.category, SUM(t.quantity) AS totalsold
    FROM transactions t JOIN products p ON t.productid=p.productid
    GROUP BY p.productid, p.productname, p.category
) AS productsales ORDER BY totalsold DESC LIMIT 5;"""},

    {"id":14,"section":"Advanced","title":"RFM scoring — NTILE window functions",
     "purpose":"Assign a 1–3 score to each RFM dimension and compute a composite RFM score.",
     "sql":"""SELECT c.customerid, c.firstname||' '||c.lastname AS fullname, s.segmentlabel,
    bm.recencyofpurchase, bm.purchasefrequency, bm.averagespending,
    NTILE(3) OVER (ORDER BY bm.recencyofpurchase ASC)  AS recencyscore,
    NTILE(3) OVER (ORDER BY bm.purchasefrequency DESC) AS frequencyscore,
    NTILE(3) OVER (ORDER BY bm.averagespending DESC)   AS monetaryscore,
    (NTILE(3) OVER (ORDER BY bm.recencyofpurchase ASC)
   + NTILE(3) OVER (ORDER BY bm.purchasefrequency DESC)
   + NTILE(3) OVER (ORDER BY bm.averagespending DESC)) AS rfm_score
FROM behavioral_metrics bm
JOIN customers c            ON bm.customerid=c.customerid
JOIN segmentation_results s ON bm.customerid=s.customerid
WHERE bm.purchasefrequency>0 ORDER BY rfm_score DESC LIMIT 50;"""},

    {"id":15,"section":"Advanced","title":"Running cumulative revenue per customer",
     "purpose":"Show a cumulative spend timeline per customer using SUM() OVER window function.",
     "sql":"""SELECT t.customerid, c.firstname||' '||c.lastname AS customername,
    t.transactiondate, t.totalamount,
    SUM(t.totalamount) OVER (
        PARTITION BY t.customerid ORDER BY t.transactiondate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulativespend
FROM transactions t JOIN customers c ON t.customerid=c.customerid
ORDER BY t.customerid, t.transactiondate LIMIT 100;"""},

    {"id":16,"section":"Advanced","title":"Full transaction history with product names",
     "purpose":"Every transaction showing customer name, product, category, quantity, and amount.",
     "sql":"""SELECT t.transactionid, t.transactiondate, c.firstname||' '||c.lastname AS customername,
    p.productname, p.category, t.quantity, t.totalamount
FROM transactions t JOIN customers c ON t.customerid=c.customerid
JOIN products p ON t.productid=p.productid ORDER BY t.transactiondate DESC LIMIT 100;"""},

    {"id":17,"section":"Advanced","title":"Customer profile with segmentation",
     "purpose":"Each customer's name alongside their assigned segment label and cluster ID.",
     "sql":"""SELECT c.customerid, c.firstname||' '||c.lastname AS customername,
    c.age, c.gender, sr.clusterid, sr.segmentlabel, sr.segmentationdate
FROM customers c JOIN segmentation_results sr ON c.customerid=sr.customerid
ORDER BY sr.clusterid, c.lastname LIMIT 100;"""},

    {"id":18,"section":"Advanced","title":"Customers with behavioral metrics (LEFT JOIN)",
     "purpose":"Each customer's purchase frequency, average spending, and recency using LEFT JOIN.",
     "sql":"""SELECT c.customerid, c.firstname||' '||c.lastname AS customername,
    c.email, bm.purchasefrequency, bm.averagespending, bm.recencyofpurchase
FROM customers c LEFT JOIN behavioral_metrics bm ON c.customerid=bm.customerid
ORDER BY bm.averagespending DESC NULLS LAST LIMIT 100;"""},

    {"id":19,"section":"Advanced","title":"Above-average total spend (nested HAVING subquery)",
     "purpose":"Use a nested subquery in HAVING to compare each customer's spend to the average.",
     "sql":"""SELECT c.customerid, c.firstname||' '||c.lastname AS customername,
    SUM(t.totalamount) AS totalspent
FROM customers c JOIN transactions t ON c.customerid=t.customerid
GROUP BY c.customerid, c.firstname, c.lastname
HAVING SUM(t.totalamount)>(
    SELECT AVG(customertotal) FROM (
        SELECT SUM(totalamount) AS customertotal FROM transactions GROUP BY customerid
    ) sub
) ORDER BY totalspent DESC LIMIT 100;"""},

    {"id":20,"section":"Advanced","title":"Top-selling product per category (RANK)",
     "purpose":"Rank products within each category and return only the #1 product per category.",
     "sql":"""SELECT category, productname, totalrevenue, totalunitssold FROM (
    SELECT p.category, p.productname, SUM(t.totalamount) AS totalrevenue,
           SUM(t.quantity) AS totalunitssold,
           RANK() OVER (PARTITION BY p.category ORDER BY SUM(t.totalamount) DESC) AS rnk
    FROM products p JOIN transactions t ON p.productid=t.productid
    GROUP BY p.category, p.productname
) ranked WHERE rnk=1;"""},

    {"id":21,"section":"Advanced","title":"Customer lifetime value with CTE",
     "purpose":"Use a CTE to compute each customer's LTV then join with segmentation data.",
     "sql":"""WITH customertlv AS (
    SELECT c.customerid, c.firstname||' '||c.lastname AS customername,
           COUNT(t.transactionid) AS totalorders,
           SUM(t.totalamount) AS lifetimevalue,
           ROUND(AVG(t.totalamount)::numeric,2) AS avgordervalue,
           (CURRENT_DATE-MAX(t.transactiondate::date)) AS dayssincelastorder
    FROM customers c JOIN transactions t ON c.customerid=t.customerid
    GROUP BY c.customerid, c.firstname, c.lastname
)
SELECT ltv.customerid, ltv.customername, ltv.totalorders, ltv.lifetimevalue,
       ltv.avgordervalue, ltv.dayssincelastorder, sr.segmentlabel
FROM customertlv ltv JOIN segmentation_results sr ON ltv.customerid=sr.customerid
ORDER BY ltv.lifetimevalue DESC LIMIT 100;"""},

    {"id":22,"section":"Advanced","title":"Trigger — prevent negative product prices",
     "purpose":"Enforce data integrity by preventing insertion of products with negative prices.",
     "static":True,
     "sql":"""CREATE OR REPLACE FUNCTION check_product_price()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.price < 0 THEN
        RAISE EXCEPTION 'Price cannot be negative';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_product_price
BEFORE INSERT ON products
FOR EACH ROW EXECUTE FUNCTION check_product_price();"""},

    {"id":23,"section":"Advanced","title":"Stored procedure — get customers by segment",
     "purpose":"Dynamically retrieve customer details based on a specified segmentation label.",
     "static":True,
     "sql":"""CREATE OR REPLACE FUNCTION get_customers_by_segment(input_segment TEXT)
RETURNS TABLE(customerid INT, firstname TEXT, lastname TEXT,
              clusterid INT, segmentlabel TEXT, segmentationdate DATE) AS $$
    SELECT c.customerid, c.firstname, c.lastname,
           s.clusterid, s.segmentlabel, s.segmentationdate
    FROM customers c JOIN segmentation_results s ON c.customerid=s.customerid
    WHERE s.segmentlabel=input_segment;
$$ LANGUAGE SQL;
-- Call: SELECT * FROM get_customers_by_segment('High Value');"""},

    {"id":24,"section":"Advanced","title":"Index on segmentlabel for faster lookups",
     "purpose":"Speed up queries that filter on segmentlabel by creating a dedicated index.",
     "static":True,
     "sql":"""CREATE INDEX idx_segmentation_segmentlabel
ON segmentation_results(segmentlabel);"""},

    {"id":25,"section":"Advanced","title":"VIEW — unified customer segmentation view",
     "purpose":"Create a virtual table combining customers, behavioral metrics, and segmentation.",
     "sql":"""SELECT c.customerid, c.firstname, c.lastname,
    b.purchasefrequency, b.averagespending, b.recencyofpurchase,
    s.clusterid, s.segmentlabel, s.segmentationdate
FROM customers c
LEFT JOIN behavioral_metrics b      ON c.customerid=b.customerid
LEFT JOIN segmentation_results s    ON c.customerid=s.customerid
LIMIT 100;""",
     "note":"To create the view: CREATE OR REPLACE VIEW customersegmentationview AS (this query without LIMIT)."},
]

# ── new queries (26+) — power the advanced dashboard features ─
EXTENDED_QUERIES = {

    # product explorer
    "product_monthly": """
        SELECT TO_CHAR(t.transactiondate,'YYYY-MM') AS month,
               SUM(t.totalamount) AS revenue,
               SUM(t.quantity)    AS units,
               COUNT(DISTINCT t.customerid) AS unique_buyers
        FROM transactions t
        JOIN products p ON t.productid=p.productid
        WHERE p.productname ILIKE '%{name}%'
        GROUP BY month ORDER BY month;
    """,

    "product_buyers": """
        SELECT c.customerid, c.firstname||' '||c.lastname AS customername,
               c.email, s.segmentlabel,
               SUM(t.totalamount) AS totalspent,
               SUM(t.quantity)    AS unitsbought,
               COUNT(t.transactionid) AS orders,
               MAX(t.transactiondate) AS lastpurchase
        FROM transactions t
        JOIN customers c            ON t.customerid=c.customerid
        JOIN products  p            ON t.productid=p.productid
        JOIN segmentation_results s ON c.customerid=s.customerid
        WHERE p.productname ILIKE '%{name}%'
        GROUP BY c.customerid, c.firstname, c.lastname, c.email, s.segmentlabel
        ORDER BY totalspent DESC LIMIT 50;
    """,

    "product_by_segment": """
        SELECT s.segmentlabel,
               COUNT(DISTINCT t.customerid) AS buyers,
               SUM(t.totalamount)           AS revenue,
               SUM(t.quantity)              AS units
        FROM transactions t
        JOIN products p             ON t.productid=p.productid
        JOIN segmentation_results s ON t.customerid=s.customerid
        WHERE p.productname ILIKE '%{name}%'
        GROUP BY s.segmentlabel ORDER BY revenue DESC;
    """,

    "product_search": """
        SELECT p.productid, p.productname, p.category, p.price,
               COALESCE(SUM(t.totalamount),0) AS totalrevenue,
               COALESCE(SUM(t.quantity),0)    AS unitssold,
               COALESCE(COUNT(DISTINCT t.customerid),0) AS uniquebuyers
        FROM products p
        LEFT JOIN transactions t ON p.productid=t.productid
        WHERE p.productname ILIKE '%{term}%' OR p.category ILIKE '%{term}%'
        GROUP BY p.productid, p.productname, p.category, p.price
        ORDER BY totalrevenue DESC LIMIT 30;
    """,

    "category_segment_heatmap": """
        SELECT p.category, s.segmentlabel,
               SUM(t.totalamount) AS revenue,
               COUNT(DISTINCT t.customerid) AS buyers
        FROM transactions t
        JOIN products p             ON t.productid=p.productid
        JOIN segmentation_results s ON t.customerid=s.customerid
        GROUP BY p.category, s.segmentlabel
        ORDER BY p.category, revenue DESC;
    """,

    # customer explorer
    "customer_search": """
        SELECT c.customerid, c.firstname||' '||c.lastname AS fullname,
               c.email, c.phone, c.gender, c.age,
               c.registrationdate, s.segmentlabel,
               bm.purchasefrequency, bm.averagespending, bm.recencyofpurchase
        FROM customers c
        LEFT JOIN segmentation_results s ON c.customerid=s.customerid
        LEFT JOIN behavioral_metrics bm  ON c.customerid=bm.customerid
        WHERE c.firstname ILIKE '%{term}%'
           OR c.lastname  ILIKE '%{term}%'
           OR c.email     ILIKE '%{term}%'
        LIMIT 20;
    """,

    "customer_transactions": """
        SELECT t.transactionid, t.transactiondate, p.productname, p.category,
               t.quantity, t.totalamount,
               SUM(t.totalamount) OVER (
                   PARTITION BY t.customerid ORDER BY t.transactiondate
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ) AS cumulativespend
        FROM transactions t
        JOIN products p ON t.productid=p.productid
        WHERE t.customerid={cid}
        ORDER BY t.transactiondate DESC;
    """,

    "customer_rfm": """
        SELECT bm.purchasefrequency, bm.averagespending, bm.recencyofpurchase,
               s.segmentlabel, s.clusterid,
               NTILE(3) OVER (ORDER BY bm.recencyofpurchase ASC)  AS recencyscore,
               NTILE(3) OVER (ORDER BY bm.purchasefrequency DESC) AS frequencyscore,
               NTILE(3) OVER (ORDER BY bm.averagespending DESC)   AS monetaryscore
        FROM behavioral_metrics bm
        JOIN segmentation_results s ON bm.customerid=s.customerid
        WHERE bm.customerid={cid};
    """,

    "customer_category_spend": """
        SELECT p.category, SUM(t.totalamount) AS spent, SUM(t.quantity) AS units
        FROM transactions t JOIN products p ON t.productid=p.productid
        WHERE t.customerid={cid}
        GROUP BY p.category ORDER BY spent DESC;
    """,

    # analytics & insights
    "monthly_revenue_all": """
        SELECT TO_CHAR(transactiondate,'YYYY-MM') AS month,
               SUM(totalamount) AS revenue,
               COUNT(DISTINCT customerid) AS active_customers,
               COUNT(transactionid) AS orders
        FROM transactions
        GROUP BY month ORDER BY month;
    """,

    "revenue_per_segment_monthly": """
        SELECT TO_CHAR(t.transactiondate,'YYYY-MM') AS month,
               s.segmentlabel,
               SUM(t.totalamount) AS revenue
        FROM transactions t JOIN segmentation_results s ON t.customerid=s.customerid
        GROUP BY month, s.segmentlabel ORDER BY month, revenue DESC;
    """,

    "repeat_vs_onetime": """
        SELECT
            CASE WHEN cnt=1 THEN 'One-time buyers'
                 WHEN cnt<=3 THEN 'Occasional (2-3×)'
                 WHEN cnt<=6 THEN 'Regular (4-6×)'
                 ELSE 'Loyal (7×+)' END AS buyer_type,
            COUNT(*) AS customers,
            ROUND(AVG(total)::numeric,2) AS avg_spend
        FROM (
            SELECT customerid, COUNT(*) AS cnt, SUM(totalamount) AS total
            FROM transactions GROUP BY customerid
        ) t GROUP BY buyer_type ORDER BY customers DESC;
    """,

    "top_customers_overall": """
        SELECT c.customerid, c.firstname||' '||c.lastname AS fullname,
               s.segmentlabel, COUNT(t.transactionid) AS orders,
               SUM(t.totalamount) AS lifetime_value,
               ROUND(AVG(t.totalamount)::numeric,2) AS avg_order,
               MAX(t.transactiondate) AS last_purchase
        FROM transactions t
        JOIN customers c            ON t.customerid=c.customerid
        JOIN segmentation_results s ON t.customerid=s.customerid
        GROUP BY c.customerid, c.firstname, c.lastname, s.segmentlabel
        ORDER BY lifetime_value DESC LIMIT 20;
    """,

    "new_customers_monthly": """
        SELECT TO_CHAR(registrationdate,'YYYY-MM') AS month,
               COUNT(*) AS new_customers
        FROM customers
        GROUP BY month ORDER BY month;
    """,

    "avg_days_between_purchases": """
        SELECT c.customerid, c.firstname||' '||c.lastname AS fullname,
               s.segmentlabel,
               COUNT(t.transactionid) AS orders,
               ROUND(
                   (MAX(t.transactiondate::date) - MIN(t.transactiondate::date))::numeric
                   / NULLIF(COUNT(t.transactionid)-1, 0), 0
               ) AS avg_days_between_orders
        FROM transactions t
        JOIN customers c            ON t.customerid=c.customerid
        JOIN segmentation_results s ON t.customerid=s.customerid
        GROUP BY c.customerid, c.firstname, c.lastname, s.segmentlabel
        HAVING COUNT(t.transactionid)>1
        ORDER BY avg_days_between_orders ASC LIMIT 30;
    """,
}
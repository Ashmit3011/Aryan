# app.py
import streamlit as st
import json
import os
from datetime import datetime, date
import qrcode
import io

# ------------------------------------------------------------------
# 1.  Animation helpers
# ------------------------------------------------------------------
from streamlit_extras.animated_fade_in import fade_in
import time

# ------------------------------------------------------------------
# 2.  File paths
# ------------------------------------------------------------------
MENU_FILE   = "menu_data.json"
ORDERS_FILE = "orders_data.json"
SETTINGS_FILE = "settings.json"
TABLES_FILE = "tables_data.json"
USERS_FILE  = "users_data.json"

# ------------------------------------------------------------------
# 3.  Initialise defaults if files missing
# ------------------------------------------------------------------
def initialize_data_files():
    for f, default in [
        (MENU_FILE, {
            "beverages": [
                {"id":"BEV001","name":"Espresso","price":2.50,"category":"Coffee","available":True,"description":"Strong black coffee","inventory":50},
                {"id":"BEV002","name":"Cappuccino","price":3.50,"category":"Coffee","available":True,"description":"Coffee with steamed milk foam","inventory":40},
                {"id":"BEV003","name":"Latte","price":4.00,"category":"Coffee","available":True,"description":"Coffee with steamed milk","inventory":40},
                {"id":"BEV004","name":"Green Tea","price":2.00,"category":"Tea","available":True,"description":"Fresh green tea","inventory":30},
                {"id":"BEV005","name":"Fresh Orange Juice","price":3.00,"category":"Juice","available":True,"description":"Freshly squeezed orange juice","inventory":25},
            ],
            "food": [
                {"id":"FOOD001","name":"Croissant","price":2.50,"category":"Pastry","available":True,"description":"Buttery French pastry","inventory":40},
                {"id":"FOOD002","name":"Chocolate Muffin","price":3.00,"category":"Pastry","available":True,"description":"Rich chocolate muffin","inventory":35},
                {"id":"FOOD003","name":"Caesar Salad","price":8.50,"category":"Salad","available":True,"description":"Fresh romaine with caesar dressing","inventory":20},
                {"id":"FOOD004","name":"Club Sandwich","price":9.00,"category":"Sandwich","available":True,"description":"Triple layer sandwich with turkey and bacon","inventory":30},
                {"id":"FOOD005","name":"Margherita Pizza","price":12.00,"category":"Pizza","available":True,"description":"Classic pizza with tomato and mozzarella","inventory":15},
            ]
        }),
        (ORDERS_FILE, []),
        (SETTINGS_FILE, {
            "cafe_name":"My Cafe",
            "barcode_url":"https://mycafe.com/menu",
            "tax_rate":0.10,
            "service_charge":0.05
        }),
        (TABLES_FILE, [{"table_number":str(i),"status":"Available"} for i in range(1,11)]),
        (USERS_FILE, [
            {"username":"admin","password":"admin123","role":"admin"},
            {"username":"staff","password":"staff123","role":"staff"}
        ])
    ]:
        if not os.path.exists(f):
            with open(f,'w') as fp:
                json.dump(default, fp, indent=2)

initialize_data_files()

# ------------------------------------------------------------------
# 4.  Load / save helpers
# ------------------------------------------------------------------
def load_json(fp): 
    try:
        with open(fp) as f: return json.load(f)
    except: return None
def save_json(fp, data): 
    with open(fp,'w') as f: json.dump(data, f, indent=2)

# ------------------------------------------------------------------
# 5.  Auth
# ------------------------------------------------------------------
def authenticate(username, password):
    users = load_json(USERS_FILE) or []
    return next((u for u in users if u["username"]==username and u["password"]==password), None)

# ------------------------------------------------------------------
# 6.  QR helper (kept for backward compat, but UI removed)
# ------------------------------------------------------------------
def generate_menu_qr(url):
    qr = qrcode.QRCode(version=1,box_size=10,border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ------------------------------------------------------------------
# 7.  Session init
# ------------------------------------------------------------------
for k in ('logged_in','user','cart','discount'):
    if k not in st.session_state:
        st.session_state[k]=[] if k=='cart' else (0.0 if k=='discount' else None)
st.session_state['logged_in'] = bool(st.session_state['user'])

# ------------------------------------------------------------------
# 8.  LOGIN PAGE
# ------------------------------------------------------------------
def login_page():
    st.title("☕ Cafe Management System – Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        user = authenticate(u,p)
        if user:
            st.session_state['logged_in']=True
            st.session_state['user']=user
            st.rerun()
        else:
            st.error("Invalid credentials")

# ------------------------------------------------------------------
# 9.  DASHBOARD
# ------------------------------------------------------------------
def dashboard_page():
    st.header("🏠 Dashboard")
    menu=load_json(MENU_FILE) or {"beverages":[],"food":[]}
    orders=load_json(ORDERS_FILE) or []
    settings=load_json(SETTINGS_FILE) or {}

    total_items = sum(len(menu[k]) for k in menu)
    total_orders  = len(orders)
    today_orders  = [o for o in orders if o.get("date")==str(date.today())]
    today_revenue = sum(o.get("total",0) for o in today_orders)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Menu Items", total_items)
    c2.metric("Total Orders", total_orders)
    c3.metric("Today's Orders", len(today_orders))
    c4.metric("Today's Revenue", f"₹{today_revenue:.2f}")

# ------------------------------------------------------------------
# 10. MENU MANAGEMENT
# ------------------------------------------------------------------
def menu_management_page():
    st.header("📋 Menu Management")
    menu = load_json(MENU_FILE) or {"beverages":[],"food":[]}

    tab1,tab2,tab3 = st.tabs(["View Menu","Add Item","Edit Items"])

    with tab1:
        st.subheader("Current Menu")
        for cat in ["beverages","food"]:
            st.write(f"### {cat.capitalize()}")
            items=menu.get(cat,[])
            if not items: st.info("No items")
            for it in items:
                st.write(f"{it['name']} — ₹{it['price']:.2f} — Inv:{it.get('inventory','N/A')} {'✅' if it['available'] else '❌'}")

    with tab2:
        st.subheader("Add New Item")
        with st.form("add_item_form"):
            typ   = st.selectbox("Type",["beverages","food"])
            name  = st.text_input("Name")
            price = st.number_input("Price",min_value=0.01,step=0.01)
            cat   = st.text_input("Category")
            desc  = st.text_area("Description")
            inv   = st.number_input("Inventory",min_value=0,step=1)
            av    = st.checkbox("Available",True)
            if st.form_submit_button("Add"):
                if name and price and cat:
                    prefix="BEV" if typ=="beverages" else "FOOD"
                    ids=[int(it["id"].replace(prefix,"")) for it in menu.get(typ,[]) if it["id"].startswith(prefix)]
                    new_id=f"{prefix}{(max(ids)+1) if ids else 1:03d}"
                    menu.setdefault(typ,[]).append({"id":new_id,"name":name,"price":float(price),"category":cat,"available":av,"description":desc,"inventory":int(inv)})
                    save_json(MENU_FILE,menu)
                    fade_in(f"✅ Added **{name}** to menu!")
                    st.rerun()

    with tab3:
        st.subheader("Edit Items")
        all=[{**it,"_type":t} for t,its in menu.items() for it in its]
        if not all: st.info("No items"); return
        sel=st.selectbox("Select item",[f"{it['name']} ({it['_type']})" for it in all])
        it=all[[f"{i['name']} ({i['_type']})" for i in all].index(sel)]
        with st.form("edit_form"):
            n,st.text_input("Name",it["name"])
            p=st.number_input("Price",value=it["price"])
            c=st.text_input("Category",it["category"])
            d=st.text_area("Description",it.get("description",""))
            inv=st.number_input("Inventory",value=it.get("inventory",0))
            av=st.checkbox("Available",it["available"])
            col1,col2=st.columns(2)
            if col1.form_submit_button("Update"):
                for i,x in enumerate(menu[it["_type"]]):
                    if x["id"]==it["id"]:
                        menu[it["_type"]][i].update({"name":n,"price":p,"category":c,"description":d,"inventory":int(inv),"available":av})
                        save_json(MENU_FILE,menu)
                        fade_in("Updated!")
                        st.rerun()
            if col2.form_submit_button("Delete"):
                menu[it["_type"]]=[x for x in menu[it["_type"]] if x["id"]!=it["id"]]
                save_json(MENU_FILE,menu)
                fade_in("Deleted!")
                st.rerun()

# ------------------------------------------------------------------
# 11. TABLE MANAGEMENT  (AUTO SYNC)
# ------------------------------------------------------------------
def table_management_page():
    st.header("🪑 Table Management")

    tables = load_json(TABLES_FILE) or []
    orders = load_json(ORDERS_FILE) or []

    def busy(tn):
        return any(o.get("table_number")==tn and o.get("status") in {"Pending","Preparing","Ready"} for o in orders)

    changed=False
    for t in tables:
        should = "Occupied" if busy(t["table_number"]) else "Available"
        if t["status"]!=should:
            t["status"]=should; changed=True
    if changed: save_json(TABLES_FILE,tables)

    status_opts=["Available","Occupied","Reserved"]
    man=False
    for idx,t in enumerate(tables):
        c1,c2,c3=st.columns([1,2,1])
        c1.write(t["table_number"])
        c2.write(t["status"])
        new=c3.selectbox("Change",status_opts,status_opts.index(t["status"]),key=f"tbl{t['table_number']}")
        if new!=t["status"]:
            tables[idx]["status"]=new; man=True
    if man:
        save_json(TABLES_FILE,tables)
        fade_in("Table statuses updated")

# ------------------------------------------------------------------
# 12. ORDER MANAGEMENT
# ------------------------------------------------------------------
def order_management_page():
    st.header("🛒 Order Management")
    menu   = load_json(MENU_FILE) or {"beverages":[],"food":[]}
    orders = load_json(ORDERS_FILE) or []
    settings=load_json(SETTINGS_FILE) or {}

    tab1,tab2=st.tabs(["New Order","Order History"])

    with tab1:
        st.subheader("Create New Order")
        col1,col2,col3=st.columns(3)
        cust = col1.text_input("Customer Name")
        tbl  = col2.text_input("Table Number (opt)")
        mail = col3.text_input("Email (bill)")

        # build flat available menu
        avail=[it for cats in menu.values() for it in cats if it.get("available",True)]

        for cat in sorted({it["category"] for it in avail}):
            st.write(f"**{cat}**")
            for it in [i for i in avail if i["category"]==cat]:
                c1,c2,c3,c4=st.columns([3,1,1,1])
                c1.write(f"{it['name']} — {it.get('description','')}")
                c2.write(f"₹{it['price']:.2f}")
                qty=c3.number_input(f"Qty{it['id']}",0,100,key=f"qty{it['id']}")
                if c4.button("Add",key=f"add{it['id']}") and qty>0:
                    if qty>it.get("inventory",0):
                        st.error(f"Only {it['inventory']} left of {it['name']}")
                    else:
                        st.session_state.cart.append({"id":it["id"],"name":it["name"],"price":it["price"],"quantity":qty,"subtotal":round(it["price"]*qty,2)})
                        st.rerun()

        if st.session_state.cart:
            st.write("---"); st.subheader("Cart")
            for idx,ci in enumerate(st.session_state.cart):
                c1,c2,c3,c4=st.columns([3,1,1,1])
                c1.write(ci["name"]); c2.write(f"₹{ci['price']:.2f}"); c3.write(f"x{ci['quantity']}"); c4.write(f"₹{ci['subtotal']:.2f}")
                if c4.button("Remove",key=f"rm{idx}"):
                    st.session_state.cart.pop(idx); st.rerun()

            sub = sum(c["subtotal"] for c in st.session_state.cart)
            disc=st.number_input("Discount ₹",0.0,float(sub),step=0.1)
            tax=settings.get("tax_rate",.1)*(sub-disc)
            sc=settings.get("service_charge",.05)*(sub-disc)
            tot=sub-disc+tax+sc
            st.write(f"Subtotal: ₹{sub:.2f} | Discount: -₹{disc:.2f} | Tax: +₹{tax:.2f} | Service: +₹{sc:.2f}")
            st.write(f"**Total: ₹{tot:.2f}**")

            pay=st.selectbox("Payment",["Unpaid","Paid","Partial"])
            if st.button("Place Order"):
                if not cust: st.error("Name required")
                elif not st.session_state.cart: st.error("Cart empty")
                else:
                    # inventory
                    for ci in st.session_state.cart:
                        for cat in menu:
                            for it in menu[cat]:
                                if it["id"]==ci["id"]:
                                    if ci["quantity"]>it["inventory"]:
                                        st.error(f"Not enough inventory for {it['name']}"); return
                                    it["inventory"]-=ci["quantity"]
                    save_json(MENU_FILE,menu)

                    new_ord={
                        "id":f"ORD{len(orders)+1:05d}",
                        "customer_name":cust,"table_number":tbl,"items":st.session_state.cart.copy(),
                        "subtotal":sub,"discount":disc,"tax":tax,"service_charge":sc,"total":tot,
                        "date":str(date.today()),"time":datetime.now().strftime("%H:%M:%S"),
                        "timestamp":datetime.now().isoformat(),"status":"Pending","payment_status":pay
                    }
                    orders.append(new_ord); save_json(ORDERS_FILE,orders)

                    st.balloons()
                    fade_in(f"🎉 Order **{new_ord['id']}** placed!")

                    # PDF & email omitted for brevity; reuse your bill_mail if needed
                    st.session_state.cart=[]; st.rerun()
        else: st.info("Add items above")

    with tab2:
        st.subheader("Order History")
        if not orders: st.info("No orders"); return
        stat=st.selectbox("Filter status",["All","Pending","Preparing","Ready","Completed","Cancelled"])
        d=st.date_input("Filter date",None)
        filt=orders
        if stat!="All": filt=[o for o in filt if o.get("status")==stat]
        if d: filt=[o for o in filt if o.get("date")==str(d)]
        filt=sorted(filt,key=lambda x:x["timestamp"],reverse=True)
        for o in filt:
            with st.expander(f"{o['id']} by {o['customer_name']} — ₹{o['total']:.2f} ({o.get('status')})"):
                st.write(f"Date: {o['date']} {o['time']} | Table: {o.get('table_number','-')}")
                for it in o['items']: st.write(f"- {it['name']} x{it['quantity']} = ₹{it['subtotal']:.2f}")
                st.write(f"Sub: ₹{o['subtotal']:.2f} | Disc: ₹{o.get('discount',0):.2f} | Tax: ₹{o.get('tax',0):.2f} | SC: ₹{o.get('service_charge',0):.2f} | **Total: ₹{o['total']:.2f}**")
                new=st.selectbox("Update",["Pending","Preparing","Ready","Completed","Cancelled"],index=["Pending","Preparing","Ready","Completed","Cancelled"].index(o.get("status","Pending")),key=f"upd{o['id']}")
                if st.button("Update",key=f"do{o['id']}"):
                    o["status"]=new; save_json(ORDERS_FILE,orders); fade_in("Status updated"); st.rerun()

# ------------------------------------------------------------------
# 13. SALES ANALYTICS
# ------------------------------------------------------------------
def sales_analytics_page():
    st.header("📊 Sales Analytics")
    orders=load_json(ORDERS_FILE) or []
    if not orders: st.info("No data"); return
    start,end=st.date_input("Range",value=[date.today().replace(day=1),date.today()])
    filt=[o for o in orders if start<=datetime.strptime(o['date'],"%Y-%m-%d").date()<=end]
    if not filt: st.warning("Empty range"); return
    revenue=sum(o['total'] for o in filt)
    st.metric("Revenue",f"₹{revenue:.2f}")
    st.metric("Orders",len(filt))
    st.metric("Avg Ticket",f"₹{(revenue/len(filt)):.2f}")

    daily={}
    for o in filt: daily[o['date']]=daily.get(o['date'],0)+o['total']
    st.subheader("Daily Revenue")
    for d,rev in sorted(daily.items()): st.write(f"{d}: ₹{rev:.2f}")

    items={}
    for o in filt:
        for it in o['items']: items[it['name']]=items.get(it['name'],0)+it['quantity']
    st.subheader("Top Items")
    for name,qty in sorted(items.items(),key=lambda x:x[1],reverse=True)[:10]:
        st.write(f"{name}: {qty} sold")

# ------------------------------------------------------------------
# 14. SETTINGS
# ------------------------------------------------------------------
def settings_page():
    st.header("⚙ Settings")
    settings=load_json(SETTINGS_FILE) or {}
    with st.form("settings"):
        cn=st.text_input("Cafe Name",settings.get("cafe_name","My Cafe"))
        url=st.text_input("Menu URL",settings.get("barcode_url","https://mycafe.com/menu"))
        tax=st.number_input("Tax %",0.,100.,settings.get("tax_rate",.1)*100,step=.1)/100
        sc=st.number_input("Service Charge %",0.,100.,settings.get("service_charge",.05)*100,step=.1)/100
        if st.form_submit_button("Save"):
            save_json(SETTINGS_FILE,{"cafe_name":cn,"barcode_url":url,"tax_rate":tax,"service_charge":sc})
            fade_in("Settings saved"); st.rerun()
    st.subheader("Data Mgmt")
    c1,c2,c3=st.columns(3)
    if c1.button("Export Menu"): st.download_button("Download",json.dumps(load_json(MENU_FILE),indent=2),"menu.json","application/json")
    if c2.button("Export Orders"): st.download_button("Download",json.dumps(load_json(ORDERS_FILE),indent=2),"orders.json","application/json")
    if c3.button("Clear All"):
        if st.checkbox("Confirm"):
            initialize_data_files()
            fade_in("Data cleared"); st.rerun()

# ------------------------------------------------------------------
# 15. MAIN ROUTER
# ------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Cafe Management System", page_icon="☕", layout="wide")
    if not st.session_state['logged_in']:
        login_page(); return

    user=st.session_state['user']
    st.sidebar.title(f"Logged in: {user['username']} ({user['role']})")

    options={
        "admin":["Dashboard","Menu Management","Order Management","Sales Analytics","Table Management","Settings","Logout"],
        "staff":["Dashboard","Order Management","Table Management","Logout"]
    }.get(user["role"],["Logout"])

    choice=st.sidebar.selectbox("Navigation",options)

    if choice=="Logout":
        st.session_state.clear()
        st.rerun()
    elif choice=="Dashboard":           dashboard_page()
    elif choice=="Menu Management":     menu_management_page()
    elif choice=="Order Management":    order_management_page()
    elif choice=="Sales Analytics":     sales_analytics_page()
    elif choice=="Table Management":    table_management_page()
    elif choice=="Settings":            settings_page()

if __name__=="__main__":
    main()


# 🧪 EngineIQ Testing Guide

## ✅ **WHAT SHOULD BE OPEN NOW:**

You should see **TWO browser tabs:**

1. **Main Search Page**: http://localhost:8000/
   - Shows: "EngineIQ" logo at top
   - Search bar in center
   - Data sources section showing counts

2. **Admin Dashboard**: http://localhost:8000/admin.html
   - Shows: Statistics (Total Documents: 1,233)
   - Upload area with drag-drop
   - Recent activity section

---

## 🎯 **TEST 1: MongoDB Query (Story 1 - Priya)**

### **In the MAIN SEARCH page:**

**Step 1:** Click in the search bar

**Step 2:** Type exactly: `MongoDB replica set primary marked stale`

**Step 3:** Click "Search" button or press Enter

### **✅ EXPECTED RESULTS:**

You should see **5 results** appear, like:

```
🏆 BEST MATCH

Understanding MongoDB Replication (Part 6/10)
Score: 0.609
Type: video
Preview: "So let's go to the hands on. [00:04:59] So let's 
create a replica set cluster..."

[View Full Content] [Open Source]
```

### **✓ SUCCESS IF:**
- ✅ Results appear in ~1-2 seconds
- ✅ You see "video" content type
- ✅ Score is around 0.6
- ✅ Preview text mentions MongoDB/replication
- ✅ Best Match badge (🏆) appears on first result

### **❌ PROBLEM IF:**
- No results appear → Check server logs
- Error message → Check Qdrant is running
- Takes >5 seconds → Normal, agent is working

---

## 🎯 **TEST 2: Kubernetes Query (Story 3 - Maria)**

### **In the MAIN SEARCH page:**

**Step 1:** Clear previous search

**Step 2:** Type exactly: `kubernetes local development setup`

**Step 3:** Click "Search"

### **✅ EXPECTED RESULTS:**

You should see **3 results** with **DIFFERENT types**:

```
1. K8s_Cluster_Overview.png
   Type: image ← IMAGE!
   Score: 0.573

2. backend-api/docs/DEPLOYMENT.md
   Type: text ← TEXT!
   Score: 0.562

3. #engineering - Adding to Sarah's excellent advice...
   Type: code ← CODE!
   Score: 0.559
```

### **✓ SUCCESS IF:**
- ✅ See IMAGE result (K8s diagram)
- ✅ See TEXT result (deployment docs)
- ✅ See CODE result (Slack discussion)
- ✅ **All 3 modalities in ONE search!** ⭐

### **❌ PROBLEM IF:**
- Only one type of result → Still works, just not as impressive
- No results → Try backup query: `kubernetes architecture`

---

## 🎯 **TEST 3: Architecture Query (Story 2 - Rajesh)**

### **In the MAIN SEARCH page:**

**Step 1:** Clear search

**Step 2:** Type: `payment processing architecture`

**Step 3:** Click "Search"

### **✅ EXPECTED RESULTS:**

Should see results about architecture/payments.

### **✓ SUCCESS IF:**
- ✅ Any results appear
- ✅ Related to architecture or systems

### **⚠️ BACKUP IF:**
If no good results, try: `architecture diagram overview`

This will show architectural content from your indexed docs.

---

## 🎯 **TEST 4: Admin Dashboard Stats**

### **Switch to ADMIN DASHBOARD tab:**

### **✅ CHECK THESE NUMBERS:**

**Total Documents:** Should show **1,233**

**Data Sources Breakdown:**
- Box: (number)
- Slack: (number)
- GitHub: (number)
- Wiki: (number)
- Videos: (number)
- Images: (number)

### **✓ SUCCESS IF:**
- ✅ Total = 1,233
- ✅ Numbers load within 2 seconds
- ✅ No error messages

---

## 🎯 **TEST 5: Live Upload (Story 4)**

### **PREPARATION:**
Find a small PDF file on your computer (any PDF, 1-5 pages)

### **In ADMIN DASHBOARD:**

**Step 1:** Look for the upload area (big box with "Drag and drop files")

**Step 2:** Drag your PDF file into that box

**Step 3:** Watch for processing message:
```
✓ File uploaded
✓ Gemini analyzing content...
✓ Generating embeddings...
✓ Indexing to Qdrant...
✓ Complete!
```

**Step 4:** Note the filename

**Step 5:** Switch to MAIN SEARCH tab

**Step 6:** Search for something in that PDF filename or topic

### **✅ EXPECTED RESULTS:**

Your newly uploaded file should appear in search results!

### **✓ SUCCESS IF:**
- ✅ Upload completes (shows success message)
- ✅ File appears in search within 30 seconds
- ✅ Can find it by searching related terms

### **❌ PROBLEM IF:**
- Upload fails → Check file size (<10MB recommended)
- Not searchable → Wait 1 minute, try again
- Error message → Check server logs

---

## 🎯 **TEST 6: Quick Queries (Below Search Bar)**

### **In MAIN SEARCH page:**

You should see buttons like:
- "high availability architecture"
- "monitor system performance"  
- "kubernetes networking"

**Step 1:** Click ANY of these buttons

**Step 2:** Search should auto-fill and run

### **✓ SUCCESS IF:**
- ✅ Query fills automatically
- ✅ Results appear
- ✅ Buttons are clickable

---

## 🎯 **TEST 7: Expand Results**

### **After any search:**

**Step 1:** Click "View Full Content" on any result

### **✅ EXPECTED BEHAVIOR:**

- Content expands to show full text
- Button changes to "Show Less"
- Content is formatted nicely (line breaks, bullets)
- Scrollable if long

### **✓ SUCCESS IF:**
- ✅ Expands smoothly
- ✅ Shows more content
- ✅ Can collapse back

---

## 🎯 **TEST 8: Agent Insights (Advanced)**

### **After any search:**

Scroll to bottom of results page.

Look for "Agent Insights" section showing:
```
Agent Insights:
✓ Documents searched: 1233
✓ Documents filtered: 127
✓ Execution path: query_parser → permission_filter → hybrid_search → rerank
✓ Time: 1.2 seconds
```

### **✓ SUCCESS IF:**
- ✅ Shows document counts
- ✅ Shows execution path (4-8 nodes)
- ✅ Shows timing

---

## 📊 **OVERALL SYSTEM HEALTH CHECK**

### **✅ ALL SYSTEMS GO IF:**

1. ✅ **Search works** (MongoDB query returns results)
2. ✅ **Multimodal works** (Kubernetes shows image+text+code)
3. ✅ **Stats load** (Admin shows 1,233 documents)
4. ✅ **Upload works** (Can add new document)
5. ✅ **UI responsive** (No lag, smooth interactions)

### **⚠️ WARNING SIGNS:**

- ❌ No results for any query → Qdrant not connected
- ❌ "Server error" messages → Check backend logs
- ❌ Stats show 0 documents → Collection not loaded
- ❌ Upload fails → Check file permissions

---

## 🚨 **IF SOMETHING BREAKS:**

### **Quick Fixes:**

**Problem:** Search returns no results
**Fix:** Check Qdrant is running:
```bash
curl http://localhost:6333/collections/knowledge_base
```

**Problem:** Server not responding
**Fix:** Restart server:
```bash
cd /Users/sreenath/Code/Function1-Hackathon-1stPrize/EngineIQ
python -m backend.api.server
```

**Problem:** Slow responses (>5 seconds)
**Fix:** Normal for agent processing, just wait

---

## 🎬 **DEMO READINESS CHECKLIST**

After testing, check off:

- [ ] MongoDB query works (returns video results)
- [ ] Kubernetes query works (returns image+text+code)
- [ ] Admin dashboard loads (shows 1,233 docs)
- [ ] Upload works (tested with sample PDF)
- [ ] Quick query buttons work
- [ ] Expand/collapse works
- [ ] Agent insights visible
- [ ] No error messages anywhere
- [ ] UI looks professional
- [ ] Stats load quickly

### **✅ IF ALL CHECKED → YOU'RE READY FOR DEMO!**

---

## 🎥 **DEMO PRACTICE SCRIPT**

Once everything works, practice this:

**Open browser with both tabs:**
1. Main search: http://localhost:8000/
2. Admin: http://localhost:8000/admin.html

**Practice flow:**
1. Type MongoDB query → Show results → Explain multimodal
2. Type Kubernetes query → Show 3 types → Explain learning styles
3. Switch to admin → Show stats → Explain scale
4. Upload PDF → Process → Search → Show new result
5. Total time: Under 5 minutes

**Time yourself!** Use phone stopwatch.

---

## 💡 **TIPS FOR TESTING:**

1. **Test each query 2-3 times** to ensure consistency
2. **Note the exact results** you get (for demo script)
3. **Screenshot any cool results** (for slides)
4. **Time your searches** (should be 1-3 seconds)
5. **Have backup queries ready** if something fails

---

## 🏆 **YOU'RE TESTING A WINNING DEMO!**

**What judges will see:**
- Real working system ✓
- Multimodal search ✓
- Real-time indexing ✓
- Professional UI ✓
- 1,233 real documents ✓

**This is NOT a mock demo - it's PRODUCTION QUALITY!**

---

**Go test it now! Report back what you see! 🚀**

"""Analytics API routes for user behavior tracking"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import Optional
import logging

from backend.database.mongodb import mongodb_client, get_conversations_collection
from backend.api.routes.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/user-stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get current user's usage statistics"""
    try:
        conversations = get_conversations_collection()
        db = mongodb_client.db
        
        # Time ranges
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total queries
        total_queries = await conversations.count_documents({"user_id": current_user["email"]})
        
        # Queries by time range
        queries_today = await conversations.count_documents({
            "user_id": current_user["email"],
            "timestamp": {"$gte": day_ago}
        })
        
        queries_this_week = await conversations.count_documents({
            "user_id": current_user["email"],
            "timestamp": {"$gte": week_ago}
        })
        
        queries_this_month = await conversations.count_documents({
            "user_id": current_user["email"],
            "timestamp": {"$gte": month_ago}
        })
        
        # Average response time
        pipeline = [
            {"$match": {"user_id": current_user["email"], "response_time": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "avg_response_time": {"$avg": "$response_time"},
                "min_response_time": {"$min": "$response_time"},
                "max_response_time": {"$max": "$response_time"}
            }}
        ]
        
        response_stats = await conversations.aggregate(pipeline).to_list(1)
        
        # Most used collections
        collection_pipeline = [
            {"$match": {"user_id": current_user["email"]}},
            {"$unwind": "$metadata.collections"},
            {"$group": {
                "_id": "$metadata.collections",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        top_collections = await conversations.aggregate(collection_pipeline).to_list(5)
        
        # Credits spent
        credit_pipeline = [
            {"$match": {"user_id": current_user["email"]}},
            {"$group": {
                "_id": None,
                "total_credits_spent": {"$sum": "$credits_used"}
            }}
        ]
        
        credit_stats = await conversations.aggregate(credit_pipeline).to_list(1)
        
        return {
            "success": True,
            "stats": {
                "queries": {
                    "total": total_queries,
                    "today": queries_today,
                    "this_week": queries_this_week,
                    "this_month": queries_this_month
                },
                "response_time": response_stats[0] if response_stats else {
                    "avg_response_time": 0,
                    "min_response_time": 0,
                    "max_response_time": 0
                },
                "top_collections": [
                    {"name": c["_id"], "count": c["count"]}
                    for c in top_collections
                ],
                "credits_spent": credit_stats[0].get("total_credits_spent", 0) if credit_stats else 0
            }
        }
        
    except Exception as e:
        logger.error(f"User stats error: {e}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı")


@router.get("/admin/platform-stats")
async def get_platform_stats(current_user: dict = Depends(require_admin)):
    """Get platform-wide statistics (admin only)"""
    try:
        conversations = get_conversations_collection()
        db = mongodb_client.db
        
        # Time ranges
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        # Total users
        total_users = await db.users.count_documents({})
        active_users_today = await conversations.distinct("user_id", {
            "timestamp": {"$gte": day_ago}
        })
        
        # Total queries
        total_queries = await conversations.count_documents({})
        queries_today = await conversations.count_documents({"timestamp": {"$gte": day_ago}})
        queries_this_week = await conversations.count_documents({"timestamp": {"$gte": week_ago}})
        
        # Average response time
        response_pipeline = [
            {"$match": {"response_time": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "avg_response_time": {"$avg": "$response_time"}
            }}
        ]
        
        response_stats = await conversations.aggregate(response_pipeline).to_list(1)
        
        # Most active users
        active_users_pipeline = [
            {"$group": {
                "_id": "$user_id",
                "query_count": {"$sum": 1},
                "total_credits": {"$sum": "$credits_used"}
            }},
            {"$sort": {"query_count": -1}},
            {"$limit": 10}
        ]
        
        top_users = await conversations.aggregate(active_users_pipeline).to_list(10)
        
        # Popular queries (most common topics)
        popular_collections_pipeline = [
            {"$unwind": "$metadata.collections"},
            {"$group": {
                "_id": "$metadata.collections",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        popular_collections = await conversations.aggregate(popular_collections_pipeline).to_list(5)
        
        # Query volume by hour (last 24 hours)
        hourly_pipeline = [
            {"$match": {"timestamp": {"$gte": day_ago}}},
            {"$group": {
                "_id": {"$hour": "$timestamp"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        hourly_data = await conversations.aggregate(hourly_pipeline).to_list(24)
        
        return {
            "success": True,
            "platform_stats": {
                "users": {
                    "total": total_users,
                    "active_today": len(active_users_today)
                },
                "queries": {
                    "total": total_queries,
                    "today": queries_today,
                    "this_week": queries_this_week
                },
                "performance": {
                    "avg_response_time": response_stats[0]["avg_response_time"] if response_stats else 0
                },
                "top_users": [
                    {
                        "email": u["_id"],
                        "queries": u["query_count"],
                        "credits_used": u["total_credits"]
                    }
                    for u in top_users
                ],
                "popular_collections": [
                    {"name": c["_id"], "count": c["count"]}
                    for c in popular_collections
                ],
                "hourly_distribution": [
                    {"hour": h["_id"], "queries": h["count"]}
                    for h in hourly_data
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Platform stats error: {e}")
        raise HTTPException(status_code=500, detail="Platform istatistikleri alınamadı")


@router.get("/trends")
async def get_query_trends(
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Get query trends over time for current user"""
    try:
        conversations = get_conversations_collection()
        
        # Date range
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        # Daily query count
        daily_pipeline = [
            {"$match": {
                "user_id": current_user["email"],
                "timestamp": {"$gte": start_date}
            }},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp"
                    }
                },
                "count": {"$sum": 1},
                "avg_response_time": {"$avg": "$response_time"},
                "total_credits": {"$sum": "$credits_used"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_data = await conversations.aggregate(daily_pipeline).to_list(days)
        
        return {
            "success": True,
            "period_days": days,
            "trends": [
                {
                    "date": d["_id"],
                    "queries": d["count"],
                    "avg_response_time": round(d.get("avg_response_time", 0), 2),
                    "credits_used": round(d.get("total_credits", 0), 4)
                }
                for d in daily_data
            ]
        }
        
    except Exception as e:
        logger.error(f"Trends error: {e}")
        raise HTTPException(status_code=500, detail="Trend verileri alınamadı")

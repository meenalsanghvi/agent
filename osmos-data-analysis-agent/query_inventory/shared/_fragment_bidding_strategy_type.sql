-- =====================================================================
-- FRAGMENT (not a standalone runnable query)
-- id:                       shared._fragment.bidding_strategy_type
-- source:                   tools/common_tools.py:1855  (fn get_campaigns_in_category, bidding_strategy_type_case)
-- agent:                    shared
-- description:              Large CASE expression that derives campaign_group_bidding_strategy_type
--                           (CPC / CPM / Max Performance CPC / Max Performance CPM / ROI / Fixed CPM /
--                           CPD / NA / UNKNOWN) from campaign_type + objective_name + bidding_strategy +
--                           campaign_subtype + JSON in campaign_setting_metadata.
-- note:                     Spliced into get_campaigns_in_category.sql at "{bidding_strategy_type_case}".
--                           Not queried on its own. {_meta} below is itself an inline sub-fragment:
--                             _meta = REPLACE(mcd.campaign_setting_metadata, '""', '"')
--                           (double-quote-escaped JSON is un-escaped before JSON_EXTRACT_SCALAR).
-- injected_fragments:
--   {_meta}  <- "REPLACE(mcd.campaign_setting_metadata, '\"\"', '\"')"
-- tables:                   (references columns of reporting.marketing_campaign_dimensions mcd; no FROM of its own)
-- =====================================================================

CASE
            WHEN (mcd.campaign_type = 'PERFORMANCE' AND mcd.objective_name IN ('Visitors', 'Visibility') AND mcd.bidding_strategy = 'AUTO_CPC') THEN 'Max Performance CPC'
            WHEN (mcd.campaign_type = 'PERFORMANCE' AND mcd.objective_name IN ('Visitors', 'Visibility') AND mcd.bidding_strategy = 'AUTO_CPM') THEN 'Max Performance CPM'
            WHEN (mcd.campaign_type = 'PERFORMANCE' AND mcd.objective_name IN ('Visitors', 'Visibility') AND mcd.bidding_strategy IN ('CPM', 'CPC')) THEN mcd.bidding_strategy
            WHEN mcd.campaign_type IN ('INVENTORY', 'AWARENESS') AND mcd.campaign_subtype = 'PRE_AUCTION' THEN 'NA'
            WHEN mcd.objective_name IN ('Absolute Revenue') THEN 'ROI'
            WHEN mcd.objective_name IN ('Visibility', 'Reach') AND mcd.campaign_subtype = 'AUCTION' THEN UPPER(JSON_EXTRACT_SCALAR({_meta}, '$.bidding_strategy_type'))
            WHEN mcd.objective_name IN ('Visibility', 'Reach') AND mcd.campaign_subtype = 'BLOCK_BUY' AND JSON_EXTRACT_SCALAR({_meta}, '$.bidding_strategy_type') = 'CPM' THEN 'Fixed CPM'
            WHEN mcd.objective_name IN ('Visibility', 'Reach') AND mcd.campaign_subtype = 'BLOCK_BUY' AND JSON_EXTRACT_SCALAR({_meta}, '$.bidding_strategy_type') = 'CPD' THEN 'CPD'
            ELSE 'UNKNOWN'
        END
